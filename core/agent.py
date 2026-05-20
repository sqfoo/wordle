import re
import json
import time
import uuid
from typing import List, TypedDict, Annotated

from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from core.llm import setup_llm
from core.solver import Solver
from core.tools import build_tools

# Settings for Exponential Retry
MAX_RETRIES = 5
BASE_WAIT = 10


class Agent:
    def __init__(self, llm_config: dict, sys_prompt: str, min_max_filter: bool = True):
        self.llm = setup_llm(llm_config)
        
        solver = Solver('./data/words.txt', min_max_filter=min_max_filter)
        tools = build_tools(solver=solver)
        self.tools = ToolNode(tools)
        self.llm_with_tools = self.llm.bind_tools(tools)
        self.system_prompt = sys_prompt
        self.thread_id = str(uuid.uuid4())

        print('Building the agent ... ...')
        self.graph = self.build_graph()

    def assistant(self, state: MessagesState): # -> Call models
        sys_msg = SystemMessage(content=self.system_prompt)
        response = self.llm_with_tools.invoke([sys_msg] + state["messages"])
        return {"messages": [response]}

    def build_graph(self):
        graph_builder = StateGraph(MessagesState)

        # 1. Explicitly name your nodes if passing objects/methods to prevent naming string mismatches
        graph_builder.add_node("assistant", self.assistant)
        graph_builder.add_node("tools", self.tools)

        graph_builder.set_entry_point("assistant")
        
        # 2. Let tools_condition completely manage the routing out of "assistant"
        graph_builder.add_conditional_edges(
            "assistant",
            tools_condition,
            {
                "tools": "tools", 
                END: END
            },
        )

        # 3. Once tools finish, they route right back to the assistant to analyze results
        graph_builder.add_edge("tools", "assistant")
        graph = graph_builder.compile()
        return graph
    
    def visualize(self):
        print('Visualise the agent workflow and saved it in workflow.png')
        self.graph.get_graph().draw_mermaid_png(output_file_path="workflow.png")

    def extract_after_final_answer(self, text: str) -> str:
        keyword = "FINAL ANSWER"
        # re.findall finds every instance of { ... }
        # [^}]* ensures we don't accidentally skip over nested structures
        matches = re.findall(r'(\{.*?\})', text, re.DOTALL)
        
        if not matches:
            return None
        
        # We take the last match [-1]
        last_json_str = matches[-1]
        
        try:
            # Replace single quotes with double quotes for valid JSON
            # (LLMs often use ' which is valid Python but invalid JSON)
            valid_json_str = last_json_str.replace("'", '"')
            data = json.loads(valid_json_str)
            return data.get(keyword)
        except json.JSONDecodeError:
            return None
    
    def __call__(self, human_message: List[dict]) -> str:
        # Formulate the payload exactly how your StateGraph expects it
        payload = {
            "messages": [{"role": "user", "content": human_message}]
        }

        for attempt in range(MAX_RETRIES):
            try:
                # Invoke the graph
                response = self.graph.invoke(payload, config={"configurable": {"thread_id": self.thread_id}})
                
                # Extract the text content safely from the final state messgae
                final_message_content = response['messages'][-1].content
                final_ans = self.extract_after_final_answer(final_message_content)
                return final_ans
            
            except Exception as e:
                # Exponential backoff calculation: 2s, 4s, 8s, 16s...
                sleep_time = BASE_WAIT * (2 ** attempt) 
                
                if attempt < MAX_RETRIES - 1:
                    print(f"Error: {str(e)}")
                    print(f"Attempt {attempt + 1} failed. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    return f"Error processing query after {MAX_RETRIES} attempts: {str(e)}"
            

    def update(self, feedback: List[dict]) -> bool:
        success = True
        for f in feedback:
            success = success and f.get("result", None) == "correct"
        return success
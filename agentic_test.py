import json, time

from dotenv import load_dotenv
load_dotenv(dotenv_path="../langchain/.env")

from core.llm import HUGGINGFACE, GEMINI
from core.agent import Agent
from core.prompts import AGENT_PROMPT

if __name__ == "__main__":
    agent = Agent(
        llm_config=HUGGINGFACE, 
        sys_prompt=AGENT_PROMPT
    )
    agent.visualize()

    playing = True
    while playing:
        tgt = input("Target Word:")
        
        for j in range(6):
            feedback = []
            if j != 0:
                for i in range(5):
                    resp = input('Feedback')
                    feedback.append(json.loads(resp))
            
            print(feedback, type(feedback))
            feedback = json.dumps(feedback)
            print((feedback), type(feedback))
            final_answer = agent(feedback)
            
            if isinstance(final_answer, bool) and final_answer:
                print('We solved it')
                break
            else:
                print(f'We guess {final_answer}')
            
            time.sleep(10)
            
        playing = bool(input('Still Playing?'))
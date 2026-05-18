import json, time

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from core.llm import HUGGINGFACE, GEMINI
from core.agent import Agent
from core.tools import update_candidate, find_the_best_guess, empty_space

SYS_PROMPT = """
You are an expert Wordle solver bot. Analyze the user's input and strictly follow this sequence:

1. CHECK FOR NEW GAME: If the input is empty, "[]", or indicates a brand new game, SKIP step 2. Call the 'find_the_best_guess' tool immediately to select an optimal opening word (like 'crane' or 'slate'), and return that as your final JSON response.

2. ONGOING GAME SEQUENCE: If there is historical feedback present:
   - First, you MUST call the 'update_candidate' tool with the feedback. Stop and wait for the tool output.
   - If 'update_candidate' returns True, the game is solved! Call 'empty_space' and return {"FINAL ANSWER": true}.
   - If 'update_candidate' returns False, call 'find_the_best_guess' to find the next best word based on the new pool.
   - If 'find_the_best_guess' returns None, retry it

Always wrap your final answer in the exact JSON format: {"FINAL ANSWER": "YOUR WORD"}
"""



if __name__ == "__main__":
    agent = Agent(
        llm_config=HUGGINGFACE, 
        tools=[update_candidate, find_the_best_guess, empty_space], 
        sys_prompt=SYS_PROMPT
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
            
            feedback = json.dumps(feedback)
            final_answer = agent(feedback)
            
            if isinstance(final_answer, bool) and final_answer:
                print('We solved it')
                break
            else:
                print(f'We guess {final_answer}')
            
            time.sleep(10)
            
        playing = bool(input('Still Playing?'))
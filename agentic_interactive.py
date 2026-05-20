import json, time

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from core.llm import HUGGINGFACE, GEMINI
from core.agent import Agent
from core.prompts import AGENT_PROMPT

VALID_FEEDBACK = ["absent", "correct", "present"]

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
                for i, c in enumerate(final_answer):
                    resp = None
                    while not isinstance(resp, str) or (isinstance(resp, str) and resp not in VALID_FEEDBACK):
                        resp = input(f'Feedback for {c} on slot {i}(specify"absent"/"correct"/"present"): ')
                    resp = {
                        "slot": i,
                        "guess": c,
                        "result": resp
                    }
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
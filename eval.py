import time
import json
import argparse
import requests
from langchain_core.messages import HumanMessage, SystemMessage

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from core.llm import HUGGINGFACE, GEMINI, setup_llm
from core.agent import Agent
from core.prompts import LLM_PROMPT, AGENT_PROMPT
from core.memory import Memory
from core.solver import Solver
from core.utils import extract_last_json
from core.settings import MODE, MAX_RETRIES

def setup_approach(args):
    approach = args.approach
    approach = approach.upper()
    
    if approach == 'AGENT':
        llm_config = globals()[args.llm_config]
        guesser = Agent(
            llm_config=llm_config,
            sys_prompt=AGENT_PROMPT,
            min_max_filter=args.min_max_filter,
        )
        guesser.visualize()

    elif approach == 'LLM':
        llm_config = globals()[args.llm_config]
        llm = setup_llm(llm_config)
        
        print('Setting up the Memory for recording the past guesses and their response')
        memory = Memory()
        guesser = (llm, memory)
    else:
        print('Setting up the algorithmic approach ...')
        guesser = Solver('./data/words.txt', min_max_filter=args.min_max_filter)
    
    return guesser


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, default='./data/test.txt', help='All Candidates word')
    parser.add_argument('--approach', type=str, default='AGENT', help='Specify which mode to solve wordle, ie. ALGO, LLM, AGENT')
    parser.add_argument('--llm_config', type=str, default="HUGGINGFACE", help="LLM config to setup the llm, specify either HUGGINGFACE or GEMINI")
    parser.add_argument('--min_max_filter', type=bool, default=False, help="Enable min_max_bounding filtering rule or not, Feel free to enable if for proper wordle game")
    args = parser.parse_args()

    approach = args.approach.upper()
    guesser = setup_approach(args=args)

    # Continue working here for Evaluation
    with open(args.filename, 'r') as f:
        words = f.read().split('\n')
    
    correct = 0
    for i, word in enumerate(words):
        print(f'Round {i+1}: {word}')
        
        if approach == 'AGENT':
            feedback = []
        elif approach == 'LLM':
            feedback = "This is the first guess"
        else:
            feedback = None

        for cnt in range(1, 1+6):
            if approach == 'AGENT':
                success = False
                feedback = json.dumps(feedback) # Stringify the list
                for attempt in range(1, 1 + MAX_RETRIES):
                    try:
                        final_answer = guesser(feedback)
                        success = True
                        break
                    except Exception as e:
                        wait = 2 ** attempt
                        print(f'Error: {e}, retrying in {wait}s')
                        time.sleep(wait)
                if not success:
                    raise RuntimeError(f'Failed to invoke the agent')
                
                if isinstance(final_answer, bool) and final_answer:
                    print(f'We solved it with {cnt} Guess')
                    break
                else:
                    print(f'Agent guessed {final_answer}')
            elif approach == 'LLM':
                success = False
                for attempt in range(1, 1+MAX_RETRIES):
                    try:
                        message = [
                            SystemMessage(content=LLM_PROMPT),
                            HumanMessage(content=f'FEEDBACK: {feedback}')
                        ]
                        response = guesser[0].invoke(message)
                        resp = response.content
                        final_answer = extract_last_json(resp)
                        print(f'LLM guessed {final_answer}')
                        success = True
                        break
                    except Exception as e:
                        wait = 2 ** attempt
                        print(f'Error: {e}, retrying in {wait}s')
                        time.sleep(wait)
                if not success:
                    raise RuntimeError(f'Failed to invoke the LLM')
            else:
                final_answer = guesser.guess()
                print(f'Heurestically guessed {final_answer}')

            
            final_answer = final_answer.lower()
            # Corresponds to send the guessed word to the SERVER, and receive the FEEDBACK
            success = False
            for attempt in range(1, 1 + MAX_RETRIES):
                try:
                    resp = requests.get(MODE['specific'].format(word, final_answer), timeout=30)

                    if resp.status_code == 200: # Success
                        success = True
                        break
                    
                    wait = 2 ** attempt
                    print(f"HTTP {resp.status_code}, retrying in {wait}s")
                    time.sleep(wait)
                
                except requests.RequestException as e:
                    wait = 2 ** attempt
                    print(f'Error: {e}, retrying in {wait}s')
                    time.sleep(wait)

            if not success:
                raise RuntimeError("Failed after retries")

            feedback = resp.json()
            if approach == 'LLM':
                result = guesser[1].update(feedback)
                feedback = guesser[1].pretty_print()
            else:
                result = guesser.update(feedback)


            if result:
                correct += 1
                print(f'{approach} guessed {final_answer} correctly within {cnt} turns')
                break
            
            time.sleep(20) # Avoid reach the rate limit
    
        print('-'*60)
        if approach == 'ALGO':
            guesser.reset()
        elif approach == 'LLM':
            guesser[1].reset()
    
    score = correct / len(words) * 100
    print(f'The {approach} approach reaches the accuracy of {score:.3} %')
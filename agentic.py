import json, time
import argparse, requests

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from core.llm import HUGGINGFACE, GEMINI
from core.agent import Agent
from core.prompts import AGENT_PROMPT
from core.settings import MODE, MAX_RETRIES

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='random', help='Wordle Playing Mode, currently supports "daily", "random", "specific" ')
    parser.add_argument('--tgt', type=str, default='adieu', help='Targeted word to guess for Specific Mode')
    parser.add_argument('--random_seed', type=int, default=42, help='Random Seed for Random Mode')
    parser.add_argument('--filename', type=str, default='words.txt', help='All Candidates word')
    parser.add_argument('--llm_config', type=str, default="HUGGINGFACE", help="LLM config to setup the llm, specify either HUGGINGFACE or GEMINI")
    parser.add_argument('--min_max_filter', action='store_true', help="Enable min_max_bounding filtering rule or not, Feel free to enable if for proper wordle game")
    args = parser.parse_args()

    llm_config = globals()[args.llm_config]
    agent = Agent(
        llm_config=llm_config, 
        sys_prompt=AGENT_PROMPT,
        min_max_filter=args.min_max_filter
    )
    agent.visualize()

    mode = args.mode.lower()
    if mode == 'specific':
        with open(args.filename, 'r') as f:
            candidates = f.read().split('\n')
        assert len(args.tgt)==5 and args.tgt.lower() in candidates, f'Please specify a valid string from the attached {args.filename}'
    
    tgt = args.tgt.lower()

    feedback = []
    for cnt in range(1, 1+6):
        # Agent guesses the word
        success = False
        feedback = json.dumps(feedback)

        for attempt in range(1, 1 + MAX_RETRIES):
            try:
                final_answer = agent(feedback)
                success = True
                break
            except Exception as e:
                wait = 2 ** attempt
                print(f'Error: {e}, retrying in {wait}s')
                time.sleep(wait)
        if not success:
            raise RuntimeError(f'Failed to invoke the agent')
        
        if isinstance(final_answer, bool) and final_answer:
            print('We solved it with {cnt} Guess')
            break
        else:
            print(f'Agent guessed {final_answer}')

        # Corresponds to send the guessed word to the SERVER, and receive the FEEDBACK
        success = False
        for attempt in range(1, 1 + MAX_RETRIES):
            try:
                if mode == 'specific':
                    resp = requests.get(MODE[mode].format(tgt, final_answer), timeout=30)
                elif mode == 'random':
                    resp = requests.get(MODE[mode].format(final_answer, args.random_seed), timeout=30)
                else:
                    resp = requests.get(MODE[mode].format(final_answer), timeout=30)

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

        # Process the FEEDBACK to JSON format, and Update the Candidate Pool
        feedback = resp.json() # list
        time.sleep(20)
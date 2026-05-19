import argparse
import requests
import time

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv(dotenv_path="../langchain/.env")

from core.llm import HUGGINGFACE, GEMINI, setup_llm
from core.memory import Memory
from core.prompts import LLM_PROMPT
from core.utils import extract_last_json
from core.settings import MODE, MAX_RETRIES

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='random', help='Wordle Playing Mode, currently supports "daily", "random", "specific" ')
    parser.add_argument('--tgt', type=str, default='adieu', help='Targeted word to guess for Specific Mode')
    parser.add_argument('--random_seed', type=int, default=42, help='Random Seed for Random Mode')
    parser.add_argument('--filename', type=str, default='words.txt', help='All Candidates word')
    parser.add_argument('--min_max_filter', action='store_true', help="Enable min_max_bounding filtering rule or not, Feel free to enable if for proper wordle game")
    args = parser.parse_args()

    llm_config = globals()[args.llm_config]
    llm = setup_llm(llm_config)

    print('Setting up the Memory for recording the past guesses and their response')
    memory = Memory()

    mode = args.mode.lower()
    if mode == 'specific':
        with open('words.txt', 'r') as f:
            candidates = f.read().split('\n')
        assert len(args.tgt)==5 and args.tgt.lower() in candidates, f'Please specify a valid string from the attached {args.filename}'
    tgt = args.tgt.lower()

    feedback = "This is the first guess"
    for cnt in range(1, 1+6):
        # LLM guesses word here
        response = None
        for attempt in range(1, 1+MAX_RETRIES):
            try:
                message = [
                    SystemMessage(content=LLM_PROMPT),
                    HumanMessage(content=f'FEEDBACK: {feedback}')
                ]
                response = llm.invoke(message)
                resp = response.content
                response = extract_last_json(resp)
                break
            except Exception as e:
                wait = 2 ** attempt
                print(f'Error: {e}, retrying in {wait}s')
                time.sleep(wait)

        if response is None:
            raise RuntimeError(f'LLM failed to be called or guess the word, please refer to the error logging')

        # Corresponds to send the guessed word to the SERVER, and receive the FEEDBACK
        success = False
        for attempt in range(1, 1+MAX_RETRIES):
            try:
                if mode == 'specific':
                    resp = requests.get(MODE[mode].format(tgt, response), timeout=30)
                elif mode == 'random':
                    resp = requests.get(MODE[mode].format(response, args.random_seed), timeout=30)
                else:
                    resp = requests.get(MODE[mode].format(response), timeout=30)

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
        
        # Process the FEEDBACK to JSON format for the next guess
        feedback = resp.json()
        result = memory.update(feedback)
        if result:
            print(f'The today answer is {response} with {cnt} Guess')
            break
        feedback = memory.pretty_print()
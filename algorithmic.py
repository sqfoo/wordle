import time
import argparse
import requests

from core.solver import Solver
from core.settings import MODE, MAX_RETRIES

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='random', help='Wordle Playing Mode, currently supports "daily", "random", "specific" ')
    parser.add_argument('--tgt', type=str, default='adieu', help='Targeted word to guess for Specific Mode')
    parser.add_argument('--random_seed', type=int, default=42, help='Random Seed for Random Mode')
    parser.add_argument('--filename', type=str, default='./data/words.txt', help='All Candidates word')
    parser.add_argument('--min_max_filter', action='store_true', help="Enable min_max_bounding filtering rule or not, Feel free to enable if for proper wordle game")
    args = parser.parse_args()
    
    mode = args.mode.lower()
    if mode == 'specific':
        with open('words.txt', 'r') as f:
            candidates = f.read().split('\n')
        assert len(args.tgt)==5 and args.tgt.lower() in candidates, f'Please specify a valid string from the attached {args.filename}'
        

    solver = Solver(args.filename, min_max_filter=args.min_max_filter)
    tgt = args.tgt.lower()
    
    for cnt in range(1, 1+6):
        # Solver heuristically guesses the word
        response = solver.guess()
        print(f'Guess {cnt}: {response}')
        
        # Corresponds to send the guessed word to the SERVER, and receive the FEEDBACK
        success = False
        for attempt in range(1, 1 + MAX_RETRIES):
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
        
        # Process the FEEDBACK to JSON format, and Update the Candidate Pool
        feedback = resp.json()
        match = solver.update(feedback)
        if match:
            print(f'The today answer is {response} with {cnt} Guess')
            break
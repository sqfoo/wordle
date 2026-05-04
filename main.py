
import argparse
import requests, time
from solver import Solver

MODE = {
    'daily': 'https://wordle.votee.dev:8000/daily?guess={}&size=5',
    'random': 'https://wordle.votee.dev:8000/random?guess={}&size=5&seed={}',
    'specific': 'https://wordle.votee.dev:8000/word/{}?guess={}',
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='random', help='Wordle Playing Mode, currently supports "daily", "random", "specific" ')
    parser.add_argument('--tgt', type=str, default='adieu', help='Targeted word to guess for Specific Mode')
    parser.add_argument('--random_seed', type=int, default=42, help='Random Seed for Random Mode')
    parser.add_argument('--filename', type=str, default='words.txt', help='All Candidates word')
    args = parser.parse_args()
    
    mode = args.mode.lower()
    if mode == 'specific':
        with open('words.txt', 'r') as f:
            candidates = f.read().split('\n')
        assert len(args.tgt)==5 and args.tgt.lower() in candidates, f'Please specify a valid string from the attached {args.filename}'
        

    solver = Solver(args.filename)
    tgt = args.tgt.lower()
    
    cnt = 0
    while cnt < 6:
        response = solver.guess()
        print(f'Guess {cnt + 1}: {response}')
        
        try:
            if mode == 'specific':
                resp = requests.get(MODE[mode].format(tgt, response), timeout=30)
            elif mode == 'random':
                resp = requests.get(MODE[mode].format(response, args.random_seed), timeout=30)
            else:
                resp = requests.get(MODE[mode].format(response), timeout=30)

            if resp.status_code != 200:
                continue
            
            feedback = resp.json()
            match = solver.update(feedback)
            cnt += 1
            if match:
                print(f'The today answer is {response} with {cnt} Guess')
                break
        except:
            time.sleep(30)
            continue
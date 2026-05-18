import argparse
import json, re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv(dotenv_path="../.env") # Remove this when git push

from core.llm import HUGGINGFACE, GEMINI, setup_llm
from core.memory import Memory

MODE = {
    'daily': 'https://wordle.votee.dev:8000/daily?guess={}&size=5',
    'random': 'https://wordle.votee.dev:8000/random?guess={}&size=5&seed={}',
    'specific': 'https://wordle.votee.dev:8000/word/{}?guess={}',
}

MAX_RETRIES = 5

SYS_PROMPT = """
    You are a smart person who knows how to play wordle game, where the goal is to guess a 5-letter word within six attempts.
    The input message would be in the format of 'Guess-{i} and FEEDBACK: {Feedback}', where {i} indicates the ith turn of guessing and 
    {Feedback} tells you several information in this order:
    1. The CORRECT FORMAT that you already know: _____, where _ means UNKNOWN yet
    2. The letters must exist:
    3. Which position could not have which letters
    4. The letters must not exist
    5. The words we have guess before
    REMARKS: Position is indexed from 0 to 4

    Based on {Feedback}, there are several rules you should follow when guessing:
    - when {i}=0, just guess "SLATE" as your answer
    - Guess the word that follows the CORRECT FORMAT, and includes the letter must exist
    - Do not guess any word that includes the letters must not exist, gueessed before or the letters put in the wrong position
    - output in this JSON format of {"final_answer": "your answer here"}

    Example 1:
    {Feedback} is:
        CORRECT FORMAT: _LA_E;
        L,A,E must exist;
        B,Z must not exist;
        Guessed Words: BLAZE
    Then, guess the final answer as SLAVE

    Example 2:
    {Feedback} is:
        CORRECT FORMAT: _____;
        M,O,E must exist;
        Position 1 must not be M; Position 2 must not be O; Position 4 must not be E;
        S, K must not exist;
        Guessed Words: SMOKE
    Then, guess the final answer as MOVER
"""

HUMAN_MSG = """
    Guess-{i} and FEEDBACK: {Feedback}
"""


def extract_last_json(text):
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
        return data.get("final_answer")
    except json.JSONDecodeError:
        return None
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='random', help='Wordle Playing Mode, currently supports "daily", "random", "specific" ')
    parser.add_argument('--tgt', type=str, default='adieu', help='Targeted word to guess for Specific Mode')
    parser.add_argument('--random_seed', type=int, default=42, help='Random Seed for Random Mode')
    parser.add_argument('--filename', type=str, default='words.txt', help='All Candidates word')
    parser.add_argument('--llm_config', type=str, default="HUGGINGFACE", help="LLM config to setup the llm, specify either HUGGINGFACE or GEMINI")
    args = parser.parse_args()

    llm_config = globals()(args.llm_config)
    llm = setup_llm(llm_config)

    print('Setting up the Memory for recording the past guesses and their response')
    memory = Memory()

    mode = args.mode.lower()
    if mode == 'specific':
        with open('words.txt', 'r') as f:
            candidates = f.read().split('\n')
        assert len(args.tgt)==5 and args.tgt.lower() in candidates, f'Please specify a valid string from the attached {args.filename}'
    tgt = args.tgt.lower()

    Feedback = "This is the first guess"
    for attempt in range(1, 1+MAX_RETRIES):
        try:
            message = [
                SystemMessage(content=SYS_PROMPT),
                HumanMessage(content=HUMAN_MSG.format(i=i, Feedback=Feedback))
            ]
            response = llm.invoke(message)
            resp = response.content
            # print(extract_json_answer(resp))
            print(extract_last_json(resp))
        
        except Exception as e:
            pass


    for i in range(1, 1+6):
        if i == 1:
            Feedback = "This is the first guess"
        else:
            success = False
            for attempt in range(1, 1+MAX_RETRIES):
                pass
            comment = []

            for i in range(5):
                res = input("Feedback: ")
                res = json.loads(res)
                comment.append(res)
            result = memory.update(comment)
            if result:
                break 
            Feedback = memory.pretty_print()
        
        print(Feedback)
        


        response = llm.invoke(message)
        resp = response.content
        # print(extract_json_answer(resp))
        print(extract_last_json(resp))
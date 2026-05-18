import time
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from core.solver import Solver

MAX_RETRY = 5
solver = Solver('./data/words.txt')

class UpdateCandidateInput(BaseModel):
    feedback: List[Dict[str, Any]] = Field(
        description="The feedback array containing Wordle character match structures"
    )

@tool(args_schema=UpdateCandidateInput)
def update_candidate(feedback: List[dict]) -> bool:
    """
    Update the candidate list of words to solve Wordle Game. This must be called when receiving json response
    
    Args:
        feedback (List[dict]): a list which consists of a dictionary

    Returns:
        bool: whether the game is solved or not
    """
    
    completed = False
    for i in range(1, MAX_RETRY+1):
        try:
            print(f"Attempting to update candidates. Feedback length: {len(feedback)}")
            completed = solver.update(feedback)
            break
        except Exception as e:
            print(f"Failed to update candidate pool: {str(e)}")
            if i < MAX_RETRY:
                print(f"Waiting {i * 5} seconds to retry...")
                time.sleep(i * 5)
            else:
                print("Max retries reached. Failed to update the candidate list.")
                return False
    return completed

@tool
def find_the_best_guess() -> str:
    """
    Always heuristically find the best guess.

    Args:
    
    Returns:
        str: the word to guess
    """

    for i in range(1, MAX_RETRY+1):
        try:
            print(f"Attempting to find the best word.")
            word = solver.guess()
            return word
        except Exception as e:
            print(f"Failed to find the best word: {str(e)}")
            if i < MAX_RETRY:
                print(f"Waiting {i * 5} seconds to retry...")
                time.sleep(i * 5)
            else:
                print("Max retries reached. Failed to guess word.")
                return None

@tool
def empty_space() -> bool:
    """
    When the game is over, we have to free up the memory of solver

    Args:

    Returns:
        bool: succeed to free up space or not
    """
    
    MAX_RETRY = 5
    success = False
    for i in range(1, MAX_RETRY+1):
        try:
            print(f"Attempting to free up the moemory for the next game.")
            solver.reset()
            success = True
            if success:
                break
        except Exception as e:
            print(f'Failed to empty memory and wait for {i*5} s to retry')
            time.sleep(i*5)
    return success
# Documentation for Building a Wordle Solver

This document describes the design and implementation of a **constrain-based SOLVER** for the **Wordle** problem. The goal is to automatically infer the hidden word using iterative guesses and feedback from an API.

## What's Wordle?

[Wordle](https://www.nytimes.com/games/wordle/index.html) is a word puzzle where the objective is to guess a hidden 5-letter english word within six attempts. 

Each guess returns per-letter feedback:

- ```correct``` (**Green**) indicates the correct letter in the correct position
- ```present``` (**Yellow**) indicates the correct letter but in the wrong position
- ```absent``` (**Gray**) indicates that letter doesn't appear beyond confirmed occurences (see note below)

### Important Semantic Detail

The ```absent``` label does not always mean the letter is globally absent. 

In cases of repeated letters:

- A letter may appear as ```present``` or ```correct``` in one position
- and ```absent``` in another position within the same guess.

For example, the targeted word is ```"apple"``` while guess is ```"allee"```, the feedback would be

```
a -> correct
l -> present
l -> absent (as only one 'l' exists)
e -> absent (as only one 'e' exists)
e -> correct
```

Therefore, the solver must track **letter frequency bound**, not just **presence/absence**.

## Approach

To do so, first we load a dictionary of valid five-letter english words from either ```words.txt``` as the initial candidates. To solve this **Wordle** problem efficiently, having a good first guess is important. Based on the provided [statistics](https://github.com/joshstephenson/Wordle-Solver), it shows that the frequency of ```"S"``` as the first letter is the highest, hence we always guess ```"slate"``` as the first word.

### Key IDEA

Based on the feedback from the submitted word, we *filter out* all the invalid word from the **candidates** and always *select the best* word from the remaining candidates. We will repeat it until solved.

### Constraints

The **solver** should maintains the following state:

#### 1, Correct Position

```python3
self.correct_pos[i] = letter or None
```

If a letter is ```correct```, it must appear at that exact position.

#### 2, Forbidden Positions (for ```present```)

```python3
self.present_pos[i] = set of letters not allowed at position i
```

If a letter is ```present```, it cannot appear in that position again.

#### 3, Required Letters

```python3
self.must_have = set()
```

Letters marked as ```present``` or ```correct``` must appear at leat once.

#### 4, Invalid Letters

```python3
self.invalid = set()
```

Letters that are confirmed absent agter accounting for duplicates.


### Filter Out

A word is a valid candidate if and only if it satisfies all contraints:

#### Rule 1: No invalid letters

```python3
# Invalid Letter
if any(c in self.invalid for c in word):
    continue
```

#### Rule 2: Match all correct positions

```python3
# Invalid Position
if any(self.correct[i] and word[i] != self.correct[i] for i in range(self.word_length)):
    continue
```

#### Rule 3: Contain all required letters

```python3
# All must have characters should exist in word
if not all(c in word for c in self.must_have):
    continue
```

#### Rule 4: No forbidden positions

```python3
bad = False
for i, letters in self.present_pos.items():
    if word[i] in letters:
        bad = True
        break
if bad:
    continue
```

For example, the targeted word is ```"apple"``` and we guess ```"state"``` this time, which indicates ```'s', 't'``` are ```absent```, ```'e'``` is ```correct``` and ```'a'``` is ```present```. Then, the following exmples corresponds to the cases above:

- ```"smile"``` as ```"s"``` doees not exist in the targeted word
- ```"axiom"``` as it does not contain the corrected ```"e"``` in the correct position
- ```"brown"``` as both presented ```"a", "e"``` do not exist
- ```"plate"``` as ```"a"``` is located wrongly from the feedback

### Heuristic Selection

To always find the best word, we always select the word which has the frequent letter in that position. To do so, we estimate how likely each letter is at each position by constructing a **Positional Frequencies** from the remaining **candidates** with

```python3
pos_cnt = [Counter() for _ in range(self.word_length)]
for w in self.word_bank:
    for i, c in enumerate(w):
        pos_cnt[i][c] += 1
```

Then, we find the **best word** which satisfies that the letter on that position is the one which has the highest frequency.

## Install the Libraries

Install related packages:

```bash
pip install -r requirements.txt
``` 

## Run it

There are three supported running modes: ```"daily", "random", "specific"``` in this program. Here are the following commands to run different modes:

```bash
# Daily puzzle
python main.py --mode daily

# Random puzzle
python main.py --mode random --random_seed 42

# Specific target (for testing)
python main.py --mode specific --tgt apple
```

Feel free to have a play on it.

## Credits and Acknowledgment

We would like to thank these developers and credit their code.

- **Votee** for providing the API and testing environment
- [Josh Stephenson](https://github.com/joshstephenson/Wordle-Solver) for the provided statistics
- [ChatGPT](https://chatgpt.com/share/69f860b3-80b4-83a5-bfe8-c117856d96b1) for the discussion about how to solve this problem

Notes:

- I have forgot the source of ```words.txt``` as it is the source file that I used before for my own **Wordle** game, so I could not cite its source here.

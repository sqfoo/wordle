from typing import List
from collections import Counter, defaultdict

class Solver:
    def __init__(self, filename: str, min_max_filter: bool = True):
        # Constant
        self.word_length = 5
        self.max_triedout = 6
        self.filename = filename
        self.init_guess = 'slate'
        self.min_max_filter = min_max_filter
        self.reset()
    
    def reset(self):
        self.cnt = 0
        self.invalid = set()
        self.correct = ['_'] * self.word_length
        self.must_have = set()
        with open(self.filename, 'r') as file:
            data = file.read().split('\n')
        self.word_bank = data
        self.present_pos = defaultdict(set)
        self.min_counts = defaultdict(int)
        self.max_counts = defaultdict(lambda: float('inf'))

    def guess(self) -> str:
        if self.cnt == 0:
            out = self.init_guess
        else:
            out = self.choose_the_best()
        self.cnt += 1
        self.word_bank.remove(out)
        return out

    def update(self, response: List[dict]) -> bool:
        present_letters = set()
        absent_letters = set()
        present_counter = defaultdict(int)
        gray_counter = defaultdict(int)

        solved = True
        for feedback in response:
            i, c, result = int(feedback["slot"]), feedback["guess"], feedback["result"]
            if result == 'absent':
                absent_letters.add(c)
                gray_counter[c] += 1
            elif result == 'present':
                present_letters.add(c)
                self.present_pos[i].add(c)
                self.must_have.add(c)
                present_counter[c] += 1
            else:
                self.correct[i] = c
                present_letters.add(c)
                self.must_have.add(c)
                present_counter[c] += 1
            
            solved = solved and result == 'correct'
        
        for c in set(present_counter) | set(gray_counter):
            present, absent = present_counter[c], gray_counter[c]
            if present > 0:
                self.min_counts[c] = max(self.min_counts[c], present)
            if absent > 0 and present > 0:
                self.max_counts[c] = present

        self.invalid.update(absent_letters - present_letters)
        self.filter()
        print(f'Current Format that guessed correctly: {''.join(self.correct)} and there are {len(self.word_bank)} candidates remaining')
        return solved

    def filter(self):
        remaining = []
        for word in self.word_bank:
            # Invalid Letter
            if any(c in self.invalid for c in word):
                continue
            
            # Invalid Position
            if any(self.correct[i] != '_' and word[i] != self.correct[i] for i in range(self.word_length)):
                continue

            # All must have characters should exist in word
            if not all(c in word for c in self.must_have):
                continue
            
            # 4. present but wrong position
            bad = False
            for i, letters in self.present_pos.items():
                if word[i] in letters:
                    bad = True
                    break
            if bad:
                continue
            
            if self.min_max_filter:
                # --- Rule 5: Handle Duplicate Upper & Lower Bounds ---
                # This handles the duplicate letter edge case. We count letter distributions
                # only for words that survived structural positioning tests.
                word_counts = Counter(word)
                # Check lower bounds (e.g., if we found two 'R's, the word must have >= 2 'R's)
                if any(word_counts[char] < min_amt for char, min_amt in self.min_counts.items()):
                    continue
                
                if any(self.max_counts[char] > 0 and word_counts[char] > max_amt for char, max_amt in self.max_counts.items()):
                    continue
            
            remaining.append(word)

        self.word_bank = remaining
    
    def choose_the_best(self) -> str:
        pos_cnt = [Counter() for _ in range(self.word_length)]

        for w in self.word_bank:
            for i, c in enumerate(w):
                pos_cnt[i][c] += 1
        
        def score(word):
            return sum(pos_cnt[i][c] for i, c in enumerate(word))

        return max(self.word_bank, key=score)
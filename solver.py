
from collections import Counter, defaultdict

class Solver:
    def __init__(self, filename):
        self.cnt = 0
        self.invalid = set()
        self.word_length = 5
        self.correct = [None] * self.word_length
        self.must_have = set()

        with open(filename, 'r') as file:
            data = file.read().split('\n')
        self.word_bank = data
        
        self.init_guess = 'slate'
        self.present_pos = defaultdict(set)
    
    def guess(self):
        if self.cnt == 0:
            out = self.init_guess
        else:
            out = self.choose_the_best()
        self.cnt += 1
        self.word_bank.remove(out)
        return out

    def update(self, response):
        present_letters = set()
        absent_letters = set()
        
        for feedback in response:
            i, c, result = feedback["slot"], feedback["guess"], feedback["result"]
            if result == 'absent':
                absent_letters.add(c)
            elif result == 'present':
                present_letters.add(c)
                self.present_pos[i].add(c)
                self.must_have.add(c)
            else:
                self.correct[i] = c
                present_letters.add(c)
                self.must_have.add(c)
        
        self.invalid.update(absent_letters - present_letters)
        self.filter()
        return all(f is not None for f in self.correct)

    def filter(self):
        remaining = []
        for word in self.word_bank:
            # Invalid Letter
            if any(c in self.invalid for c in word):
                continue
            
            # Invalid Position
            if any(self.correct[i] and word[i] != self.correct[i] for i in range(self.word_length)):
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
            remaining.append(word)

        self.word_bank = remaining
    
    def choose_the_best(self):
        pos_cnt = [Counter() for _ in range(self.word_length)]

        for w in self.word_bank:
            for i, c in enumerate(w):
                pos_cnt[i][c] += 1
        
        def score(word):
            return sum(pos_cnt[i][c] for i, c in enumerate(word))

        return max(self.word_bank, key=score)
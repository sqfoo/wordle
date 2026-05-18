from collections import Counter, defaultdict

CORRECT_TEMPLATE = "CORRECT FORMAT: {correct_string}"
MUST_HAVE_TEMPLATE = "{cs} must exist"
PRESENT_TEMPLATE = "Position {pos} must not be {c}; "
MISSING_TEMPLATE = "{cs} must not exist"
GUESSED_TEMPLATE = "Gueesed Words: {words}"

class Memory:
    def __init__(self):
        self.word_length = 5
        self.invalid = set()
        self.correct = ['_'] * self.word_length
        self.must_have = set()
        self.present_pos = defaultdict(set)
        self.gueesed = []

    def update(self, response: dict) -> bool:
        present_letters = set()
        absent_letters = set()
        
        words = ''
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
            words += c

        self.gueesed.append(words)        
        self.invalid.update(absent_letters - present_letters)
        return all(f != '_' for f in self.correct)

    def pretty_print(self) -> str:
        present_string = ""
        for pos, c in self.present_pos.items():
            present_string += PRESENT_TEMPLATE.format(c=','.join(c), pos=pos)
        
        return f"""
        {CORRECT_TEMPLATE.format(correct_string=''.join(self.correct))};
        {MUST_HAVE_TEMPLATE.format(cs=','.join(self.must_have))};
        {present_string}
        {MISSING_TEMPLATE.format(cs=','.join(self.invalid))};
        {GUESSED_TEMPLATE.format(words=','.join(self.gueesed))}
        """

MODE = {
    'daily': 'https://wordle.votee.dev:8000/daily?guess={}&size=5',
    'random': 'https://wordle.votee.dev:8000/random?guess={}&size=5&seed={}',
    'specific': 'https://wordle.votee.dev:8000/word/{}?guess={}',
}

MAX_RETRIES = 5
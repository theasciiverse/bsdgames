"""Records asciiverse/casts/hangman.cast: hangman started the way av starts
it, in a folder with the bundled word list (`hangman -d words`), played by
a guesser that knows the same list. It keeps the words that fit the
pattern on screen and the misses so far, and guesses the letter most of
them contain, so it usually gets the word with a miss or two. Enter quits."""
import os
import re
from collections import Counter

from rec import Rec

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS_DIR = os.path.join(os.path.dirname(HERE), "hangman")
WORDS = [w for w in open(os.path.join(WORDS_DIR, "words")).read().split() if len(w) >= 6]
SECONDS = 42

r = Rec("hangman", "Hangman", ["-d", "words"], cwd=WORDS_DIR)
r.wait_for("Word:", 8)
r.pump(1.2)


def pattern():
    m = re.search(r"Word: ([a-z-]+)", r.text())
    return m.group(1) if m else None


tried = set()
last = None
while r.elapsed() < SECONDS:
    word = pattern()
    if word is None or ("-" not in word):
        r.pump(0.2)
        continue
    if word.count("-") == len(word) and last and last != word and tried:
        tried = set()          # a new word started
    last = word
    known = set(word) - {"-"}
    wrong = tried - known
    regex = re.compile("^" + "".join(c if c != "-" else f"[^{''.join(sorted(known)) or '-'}]" for c in word) + "$")
    cands = [w for w in WORDS if len(w) == len(word) and regex.match(w) and not (set(w) & wrong)]
    counts = Counter(c for w in cands for c in set(w) if c not in tried)
    if not counts:
        counts = Counter(c for c in "etaoinsrhldcumfpgwybvkxjqz" if c not in tried)
    guess = counts.most_common(1)[0][0]
    tried.add(guess)
    r.key(guess, 0.75)
    t = r.text()
    if "You got it" in t or "Sorry" in t:
        r.pump(2.2)            # the result, then the next word comes up
        tried = set()
        last = None
r.pump(1.0)
r.finish(b"\n")

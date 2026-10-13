"""Records asciiverse/casts/cribbage.cast: a few hands of cribbage against
the computer. The driver reads its hand off the screen (a row of ranks over
a row of suits, the cursor marked with a dot), discards to the crib the two
cards that leave the best four (fifteens, pairs, runs, flush), plays out the
pegging with Space (cribbage skips cards that would pass 31) and pauses on
the show so the scoring can be read."""
import itertools, re

from rec import Rec

SECONDS = 50
RANKS = {"A": 1, "J": 11, "Q": 12, "K": 13}

r = Rec("cribbage", "Cribbage")
r.wait_for("Discard")
r.pump(1.2)


def rank(t):
    return RANKS.get(t) or int(t)


def hand():
    """[(rank, suit)] and the cursor's index, from the first rank row with a
    suit row under it."""
    rows = r.rows()
    for y in range(len(rows) - 1):
        top, low = rows[y][28:50], rows[y + 1][28:50]
        suits = re.findall(r"\.?[SDCH]", low)
        ranks = top.split()
        if suits and len(ranks) == len(suits) and all(re.fullmatch(r"A|[2-9]|10|J|Q|K", t) for t in ranks):
            cards = [(rank(t), s[-1]) for t, s in zip(ranks, suits)]
            cur = next((i for i, s in enumerate(suits) if s.startswith(".")), 0)
            return cards, cur
    return [], 0


def points(cards):
    vals = [min(c[0], 10) for c in cards]
    p = sum(2 for n in range(2, 5) for s in itertools.combinations(vals, n) if sum(s) == 15)
    p += sum(2 for a, b in itertools.combinations([c[0] for c in cards], 2) if a == b)
    rs = sorted(c[0] for c in cards)
    for n in (4, 3):
        runs = [s for s in itertools.combinations(rs, n) if all(b - a == 1 for a, b in zip(s, s[1:]))]
        if runs:
            p += n * len(runs)
            break
    if len({c[1] for c in cards}) == 1:
        p += 4
    return p


def keep_best(cards):
    """Indexes of the two cards to discard."""
    best = max(itertools.combinations(range(len(cards)), 2),
               key=lambda d: points([c for i, c in enumerate(cards) if i not in d]))
    return best


def step(k, wait=1.0):
    r.key(k, 0.1)
    r.pump(wait)


discard = None
while r.elapsed() < SECONDS:
    text = r.text()
    cards, cur = hand()
    if len(cards) == 6 and "Discard" in text:
        discard = sorted(keep_best(cards), reverse=True)
    if discard and len(cards) > 4:
        target = discard[6 - len(cards)] if len(cards) in (5, 6) else 0
        # after the first discard the cards to its right move one left
        while cur != target:
            step("k" if cur < target else "j", 0.25)
            cur += 1 if cur < target else -1
        step(" ", 0.9)
        if len(cards) == 5:
            discard = None
        continue
    if not cards and "Press space for show" in text:
        r.pump(1.0)
        step(" ", 3.5)           # the show, or the next deal: time to read it
        continue
    step(" ", 1.0)

# quit at the next card choice
for _ in range(6):
    cards, _ = hand()
    if cards and len(cards) <= 6:
        break
    step(" ", 0.6)
r.finish(b"q")

"""Records asciiverse/casts/worm.cast: the full 100x30 field, played by a
driver that reads it off the screen. It takes the shortest way to the
number through empty cells and grass, and only into a pocket with room
for its whole length, so it grows without boxing itself in. A key is
sent only to change direction; the worm keeps going the way it last
went. It quits with q after SECONDS."""
from collections import deque

from rec import Rec, UP, DOWN, LEFT, RIGHT

SECONDS = 42
KEYS = {(-1, 0): UP, (1, 0): DOWN, (0, -1): LEFT, (0, 1): RIGHT}

r = Rec("worm", "Worm")
r.wait_for("Worm")
r.pump(1.0)


def field():
    """(head, free cells, number) in screen coordinates; free cells are
    empty or grass, inside the box."""
    rows = r.rows()
    head, goal, free = None, None, set()
    for y in range(2, 29):
        for x in range(1, 98):
            ch = rows[y][x]
            if ch == "@":
                head = (y, x)
            elif ch.isdigit():
                goal = (y, x)
                free.add((y, x))
            elif ch in ' "':
                free.add((y, x))
    return head, free, goal


def room(start, free, limit):
    seen = {start}
    q = deque([start])
    while q and len(seen) < limit:
        y, x = q.popleft()
        for dy, dx in KEYS:
            n = (y + dy, x + dx)
            if n in free and n not in seen:
                seen.add(n)
                q.append(n)
    return len(seen)


def first_step(head, goal, free):
    seen = {head: None}
    q = deque([head])
    while q:
        p = q.popleft()
        if p == goal:
            while seen[p] != head:
                p = seen[p]
            return (p[0] - head[0], p[1] - head[1])
        for d in KEYS:
            n = (p[0] + d[0], p[1] + d[1])
            if n in free and n not in seen:
                seen[n] = p
                q.append(n)
    return None


heading = None
length = 8
while r.elapsed() < SECONDS:
    r.pump(0.03)
    if "game is over" in r.text():
        break
    head, free, goal = field()
    if head is None:
        continue
    words = r.rows()[0].split()
    if "Length:" in words:
        length = int(words[words.index("Length:") + 1])
    step = first_step(head, goal, free) if goal else None
    if step:
        n = (head[0] + step[0], head[1] + step[1])
        if room(n, free, length + 20) < length + 20:
            step = None
    if step is None:
        # no safe way to the number: the roomiest free neighbour
        options = [(room((head[0] + d[0], head[1] + d[1]), free, 400), d) for d in KEYS
                   if (head[0] + d[0], head[1] + d[1]) in free]
        if options:
            step = max(options)[1]
    if step and step != heading:
        heading = step
        r.key(KEYS[step], 0.02)

r.pump(1.0)
r.finish(b"q")

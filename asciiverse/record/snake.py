"""Records asciiverse/casts/snake.cast: the full 100x30 field, played by a
driver that reads it off the screen. It walks the shortest safe way to the
money, keeping clear of the snake's head and body, and after SECONDS
heads for the exit (#) to win. A key is sent only to change direction,
since the game keeps you moving the way you last went."""
from collections import deque

from rec import Rec, UP, DOWN, LEFT, RIGHT

SECONDS = 32
KEYS = {(-1, 0): UP, (1, 0): DOWN, (0, -1): LEFT, (0, 1): RIGHT}

r = Rec("snake", "Snake")
r.wait_for("lqq")
r.pump(1.0)


def field():
    """(me, snake cells, money, exit, walls) in screen coordinates."""
    me, snake, money, goal = None, set(), None, None
    for y, row in enumerate(r.rows()):
        for x, ch in enumerate(row):
            c = r.screen.buffer[y][x]
            if ch == "@" and c.fg == "red":
                me = (y, x)
            elif ch in "@s" and c.fg == "green":
                snake.add((y, x))
            elif ch == "$":
                money = (y, x)
            elif ch == "#" and c.fg == "cyan":
                goal = (y, x)
    return me, snake, money, goal


def danger(snake):
    """The snake's cells and every cell next to one: it can step there."""
    out = set(snake)
    for y, x in snake:
        for dy, dx in KEYS:
            out.add((y + dy, x + dx))
    return out


def inside(p):
    return 2 <= p[0] <= 28 and 1 <= p[1] <= 98


def path(me, target, blocked):
    """First step of a shortest path from me to target around blocked."""
    seen = {me: None}
    q = deque([me])
    while q:
        p = q.popleft()
        if p == target:
            while seen[p] != me and seen[p] is not None:
                p = seen[p]
            return (p[0] - me[0], p[1] - me[1])
        for d in KEYS:
            n = (p[0] + d[0], p[1] + d[1])
            if n not in seen and inside(n) and (n not in blocked or n == target):
                seen[n] = p
                q.append(n)
    return None


heading = None
while r.elapsed() < 55:
    r.pump(0.03)
    me, snake, money, goal = field()
    if me is None:
        if "won" in r.text() or "eaten" in r.text():
            break
        continue
    target = goal if r.elapsed() > SECONDS or money is None else money
    blocked = danger(snake)
    step = path(me, target, blocked) or path(me, target, snake)
    if step is None:
        # nowhere safe to go: any free neighbour
        step = next((d for d in KEYS if inside((me[0] + d[0], me[1] + d[1]))
                     and (me[0] + d[0], me[1] + d[1]) not in blocked), heading)
    if step and step != heading:
        heading = step
        r.key(KEYS[step], 0.02)

r.pump(3.0)
r.finish(None)

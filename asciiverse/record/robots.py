"""Records asciiverse/casts/robots.cast: robots played by a driver that
reads the field off the screen and simulates the game's own rules (every
robot steps one cell toward you; robots that meet, or step on a heap,
become junk). It tries each of the eight moves and standing still, keeps
those that survive this turn and still leave a safe move next turn,
prefers the one that crashes the most robots, then the one furthest from
them, and teleports (t) only when trapped. When the robots get it, the
score table shows for a moment before the game exits; a game still
going at the end is quit with q, which shows the table the same way."""
from rec import Rec

SECONDS = 44
FW, FH = 58, 22                 # the field inside the 60x24 window's border
KEYS = {(0, -1): "k", (1, -1): "u", (1, 0): "l", (1, 1): "n", (0, 1): "j",
        (-1, 1): "b", (-1, 0): "h", (-1, -1): "y", (0, 0): "."}
r = Rec("robots", "Robots")
r.wait_for("Directions", 8)
r.pump(1.5)


def field():
    """(player, robots, heaps) in field coordinates."""
    rows = r.rows()
    top = (len(rows) - 24) // 2             # the 80x24 block is centred:
    left = (len(rows[0]) - 80) // 2         # robots.c, centered_origin
    me, robots, heaps = None, [], set()
    for y in range(FH):
        line = rows[top + 1 + y]
        for x in range(FW):
            c = line[left + 1 + x]
            if c == "@":
                me = (x, y)
            elif c == "+":
                robots.append((x, y))
            elif c == "*":
                heaps.add((x, y))
    return me, robots, heaps


def sign(v):
    return (v > 0) - (v < 0)


def step(me, robots, heaps, d):
    """The game after moving d: (player, robots, heaps, crashed) or None if dead."""
    p = (me[0] + d[0], me[1] + d[1])
    if not (0 <= p[0] < FW and 0 <= p[1] < FH) or p in heaps:
        p = me                  # the game ignores a blocked move
    moved = [(x + sign(p[0] - x), y + sign(p[1] - y)) for x, y in robots]
    heaps = set(heaps)
    left, seen, crashed = [], {}, 0
    for q in moved:
        seen[q] = seen.get(q, 0) + 1
    for q, n in seen.items():
        if n > 1 or q in heaps:
            if q not in heaps:
                heaps.add(q)
            crashed += n
        else:
            left.append(q)
    if p in heaps or p in left:
        return None
    return p, left, heaps, crashed


def choose(me, robots, heaps):
    best, best_key = None, None
    for d, k in KEYS.items():
        nxt = step(me, robots, heaps, d)
        if not nxt:
            continue
        p, left, h, crashed = nxt
        safe_next = not left or any(step(p, left, h, d2) for d2 in KEYS)
        if not safe_next:
            continue
        near = min((max(abs(p[0] - x), abs(p[1] - y)) for x, y in left), default=99)
        key = (crashed, min(near, 4), -abs(p[0] - FW // 2) - abs(p[1] - FH // 2))
        if best_key is None or key > best_key:
            best, best_key = k, key
    return best


while r.elapsed() < SECONDS:
    if "Top Scores" in r.text():
        r.pump(2.5)
        r.finish(b" ")
        break
    me, robots, heaps = field()
    if me is None:
        r.pump(0.2)
        continue
    k = choose(me, robots, heaps)
    r.key(k or "t", 0.35 if k else 0.8)
else:
    r.pump(1.0)
    r.key("q", 0.3)             # quitting shows the score table too
    r.wait_for("Top Scores", 4)
    r.pump(2.5)
    r.finish(b" ")

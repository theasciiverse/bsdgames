"""Records asciiverse/casts/dab.cast: dots and boxes against the computer on
a 7 by 7 field (dab 5). The driver reads the drawn edges off the screen and
plays a simple sound game: it takes any box with three sides, otherwise
draws a side that gives nothing away, and when none is left the side that
gives away the least. It walks the cursor there with hjkl and sets the side
with Space, then waits for the computer's turn to settle."""
import time

from rec import Rec

SECONDS = 46
LEVEL = 5
FW = LEVEL + 2                # boxes per side
W = FW * 2 + 1                # dab.c: the field window, w by w
ROWS = 30

r = Rec("dab", "Dots and Boxes", args=[str(LEVEL)])
r.pump(1.0)
TOP, LEFT = (ROWS - (W + 1)) // 2, (100 - W) // 2   # create_field_window: centered_origin (w+1, w)


def width(l):
    return FW + l % 2


def edge_at(l, c):
    """Screen cell of edge (l, c): even l are horizontal, odd l vertical."""
    return TOP + l, LEFT + c * 2 + (0 if l % 2 else 1)


def edges():
    rows = r.rows()
    return {(l, c) for l in range(2 * FW + 1) for c in range(width(l))
            if rows[edge_at(l, c)[0]][edge_at(l, c)[1]] != " "}


def sides(l, c):
    """The four edges of box (l, c)."""
    return [(2 * l, c), (2 * l + 1, c), (2 * l + 1, c + 1), (2 * l + 2, c)]


def boxes_of(e):
    l, c = e
    if l % 2 == 0:
        return [(b, c) for b in (l // 2 - 1, l // 2) if 0 <= b < FW]
    return [(l // 2, b) for b in (c - 1, c) if 0 <= b < FW]


def choose(have):
    free = [(l, c) for l in range(2 * FW + 1) for c in range(width(l)) if (l, c) not in have]
    if not free:
        return None
    count = lambda b: sum(s in have for s in sides(*b))
    for e in free:                                    # close a box
        if any(count(b) == 3 for b in boxes_of(e)):
            return e
    safe = [e for e in free if all(count(b) < 2 for b in boxes_of(e))]
    if safe:                                          # give nothing away
        return min(safe, key=lambda e: (sum(count(b) for b in boxes_of(e)), e))
    return min(free, key=lambda e: sum(count(b) == 2 for b in boxes_of(e)))


def settle(quiet=0.7, limit=4.0):
    """Wait until the screen stops changing (the computer has moved)."""
    end = time.time() + limit
    last, still = r.text(), time.time()
    while time.time() < end:
        r.pump(0.05)
        now = r.text()
        if now != last:
            last, still = now, time.time()
        elif time.time() - still >= quiet:
            return


cur = [0, 0]                  # _lastMove[HUMAN]: the cursor, which dab never draws


def move_to(l, c):
    while cur[0] != l:
        if cur[0] < l:
            r.key("j", 0.05)
            cur[0] += 1
        else:
            r.key("k", 0.05)
            cur[0] -= 1
        if cur[1] >= width(cur[0]):
            cur[1] -= 1
    while cur[1] != c:
        r.key("l" if cur[1] < c else "h", 0.05)
        cur[1] += 1 if cur[1] < c else -1


settle()
while r.elapsed() < SECONDS:
    e = choose(edges())
    if e is None:                                     # field full: a key goes on
        r.pump(1.5)
        break
    move_to(*e)
    r.key(" ", 0.1)
    settle()

# the computer's turn ends with flushinp(), which eats a q typed while it
# thinks, so keep asking until the game has gone
for _ in range(10):
    r.key(b"q", 0)
    if not r.pump(0.8):
        break
r.finish(None)

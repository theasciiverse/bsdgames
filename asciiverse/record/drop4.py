"""Records asciiverse/casts/drop4.cast: a game of falling tetrominoes. The
driver reads the well off the screen (blocks are reverse-video cells), turns
the new piece through its rotations to learn its shapes, tries every
rotation and column against the pile, and drops it where the pile scores
best (lines cleared, few holes, low and even). Quits with q, then Enter on
the score table."""
import time

from rec import Rec, ENTER

SECONDS = 44
B_ROWS, B_COLS, BOARD_COL = 23, 12, 28   # drop4.c: the well in its 80x24 window
SCORE_COL = 80 - 16 - 1

r = Rec("drop4", "Drop4")
r.wait_for("Score:")
r.pump(0.5)


def origin():
    """Top left of the game's 80x24 window on the 100x30 screen."""
    for y, row in enumerate(r.rows()):
        x = row.find("Score:")
        if x >= 0:
            return y - 2, x - (SCORE_COL + 2)
    return 0, 0


OY, OX = origin()


def grid():
    """Occupied cells of the well, the falling piece included."""
    cells = set()
    for y in range(B_ROWS):
        line = r.screen.buffer[OY + y]
        for x in range(B_COLS):
            if line[OX + BOARD_COL + 2 * x].reverse:
                cells.add((y, x))
    return cells


def norm(cells):
    my = min(y for y, _ in cells)
    mx = min(x for _, x in cells)
    return frozenset((y - my, x - mx) for y, x in cells)


def drop(pile, shape, x0):
    """The pile after dropping shape with its left edge at column x0, and
    the lines that cleared, or None when it does not fit."""
    if any(not 0 <= x + x0 < B_COLS for _, x in shape):
        return None
    y0 = 0
    while all((y + y0 + 1, x + x0) not in pile and y + y0 + 1 < B_ROWS for y, x in shape):
        y0 += 1
    placed = pile | {(y + y0, x + x0) for y, x in shape}
    if any(y < 0 or (y, x) in pile for y, x in placed - pile):
        return None
    full = [y for y in range(B_ROWS) if all((y, x) in placed for x in range(B_COLS))]
    if full:
        kept = set()
        for y, x in placed:
            if y not in full:
                kept.add((y + sum(1 for f in full if f > y), x))
        placed = kept
    return placed, len(full)


def score(pile, lines):
    heights = []
    holes = 0
    for x in range(B_COLS):
        col = [y for y in range(B_ROWS) if (y, x) in pile]
        top = min(col) if col else B_ROWS
        heights.append(B_ROWS - top)
        holes += sum(1 for y in range(top, B_ROWS) if (y, x) not in pile)
    bump = sum(abs(a - b) for a, b in zip(heights, heights[1:]))
    return -0.51 * sum(heights) + 0.76 * lines - 0.36 * holes - 0.18 * bump


def settle(t=0.06):
    r.pump(t)


pile = set()
while r.elapsed() < SECONDS:
    piece = grid() - pile
    if len(piece) != 4:
        settle(0.05)
        continue
    # learn the rotations: k turns the piece in place
    shapes = [norm(piece)]
    for _ in range(3):
        r.key("k", 0.07)
        p = grid() - pile
        if len(p) == 4:
            shapes.append(norm(p))
    r.key("k", 0.07)  # back to the first rotation
    best = None
    for rot, shape in enumerate(shapes):
        if shape in shapes[:rot]:
            continue
        for x0 in range(B_COLS):
            res = drop(pile, shape, x0)
            if res:
                s = score(*res)
                if best is None or s > best[0]:
                    best = (s, rot, x0, res[0])
    if best is None:
        break
    _, rot, x0, after = best
    for _ in range(rot):
        r.key("k", 0.09)
    for _ in range(14):
        p = grid() - pile
        if len(p) != 4:
            settle(0.03)
            continue
        left = min(x for _, x in p)
        if left == x0:
            break
        r.key("l" if left < x0 else "j", 0.08)
    r.key(" ", 0.12)
    pile = after
    # wait for the next piece to appear above the pile
    end = time.time() + 1.5
    while time.time() < end and len(grid() - pile) != 4:
        settle(0.03)
    r.pump(0.15)

r.key("q", 1.0)
r.finish(ENTER)

"""Records asciiverse/casts/gomoku.cast: a game against gomoku's computer,
played by a small evaluator that reads the board off the screen. For each
empty point near the stones it scores every line of five through it,
counting its own stones and the computer's, so it completes its own fours,
blocks the computer's threes and fours, and otherwise builds its longest
line. Whose stone is whose comes from the colours: the player's are cyan,
the computer's magenta. A game still going near the end is resigned with q,
which ends the program."""
from rec import Rec, UP, DOWN, LEFT, RIGHT

N = 19
SECONDS = 55
r = Rec("gomoku", "Gomoku")
r.wait_for("Your move", 8)
r.pump(1.2)

# my line of k stones is worth MINE[k], the computer's THEIRS[k]
MINE = [0, 2, 12, 150, 2500, 10**7]
THEIRS = [0, 1, 10, 200, 6000, 10**6]


def board():
    """(grid, origin, cursor): grid[y][x] is 'me', 'pc' or None, from the
    19x19 points inside the box, with the cursor where the cyan-backed
    point is."""
    buf = r.screen.buffer
    rows = r.rows()
    top = next(y for y, l in enumerate(rows) if "lqqqq" in l or "┌────" in l)
    left = min(i for i in (rows[top].find("lqqqq"), rows[top].find("┌────")) if i >= 0)
    grid, cur = [], None
    for j in range(N):
        row = []
        for i in range(N):
            c = buf[top + 1 + j][left + 2 + 2 * i]
            colours = (c.fg, c.bg)
            who = None
            if c.data in "XO":
                who = "me" if "cyan" in colours else "pc"
            if c.bg == "cyan":
                cur = (j, i)
            row.append(who)
        grid.append(row)
    return grid, cur


DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]


def score(grid, y, x):
    s = 0
    for dy, dx in DIRS:
        for back in range(5):
            cells = [(y + (k - back) * dy, x + (k - back) * dx) for k in range(5)]
            if not all(0 <= a < N and 0 <= b < N for a, b in cells):
                continue
            who = [grid[a][b] for a, b in cells]
            me, pc = who.count("me"), who.count("pc")
            if pc == 0:
                s += MINE[me + 1]
            if me == 0:
                s += THEIRS[pc + 1] if pc else 0
    return s


def best(grid):
    stones = [(y, x) for y in range(N) for x in range(N) if grid[y][x]]
    if not stones:
        return N // 2, N // 2
    cand = {(y + dy, x + dx) for y, x in stones for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)
            if 0 <= y + dy < N and 0 <= x + dx < N and not grid[y + dy][x + dx]}
    # prefer the middle on ties, so the game stays in view
    return max(cand, key=lambda p: (score(grid, *p), -abs(p[0] - 9) - abs(p[1] - 9)))


def go(cur, to):
    (cy, cx), (ty, tx) = cur, to
    while cy < ty: r.key(DOWN, 0.035); cy += 1
    while cy > ty: r.key(UP, 0.035); cy -= 1
    while cx < tx: r.key(RIGHT, 0.035); cx += 1
    while cx > tx: r.key(LEFT, 0.035); cx -= 1


while r.elapsed() < SECONDS:
    text = r.text()
    if "won" in text or "tie" in text:
        r.pump(3.0)              # the result stays up for a moment
        r.finish(b" ")
        break
    if "Your move" not in text:
        r.pump(0.2)
        continue
    grid, cur = board()
    if cur is None:
        r.pump(0.2)
        continue
    target = best(grid)
    r.pump(0.3)                  # a moment to look at the computer's move
    go(cur, target)
    r.key(" ", 0.2)
    r.wait_for("Your move", 6)
else:
    r.pump(1.5)
    r.finish(b"q")

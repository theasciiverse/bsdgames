"""Records asciiverse/casts/spirhunt.cast: Space Pirate Hunt played by a
driver that reads the panel. When pirates (P) are in the sector it fires
plasers at them, or a torpedo every other fight; otherwise it warps to the
nearest quadrant the galaxy map shows pirates in, or to an unscanned one
to look. It quits with Q after SECONDS.

Panel layout at 100x30 (ui.c create_windows): the sector scan's cells are
at row 19 + y, column 15 + 2x; the galaxy map's quadrant x, y has its
starbase mark at row 19 + y, column 37 + 3x and its pirate count just
right of it; the current quadrant is drawn reversed."""
import random

from rec import Rec, ENTER

SECONDS = 48

r = Rec("spirhunt", "Space Pirate Hunt")
r.wait_for("PIRATE HUNT")
r.pump(2.5)


def typed(text, pause=1.4):
    for ch in text:
        r.key(ch, 0.09)
    r.key(ENTER, pause)


def prompt():
    """The question on the command line, if one is waiting."""
    return r.rows()[28][36:].strip()


def pirates_here():
    out = []
    for y in range(10):
        for x in range(10):
            if r.rows()[19 + y][15 + 2 * x] == "P":
                out.append((x, y))
    return out


def galaxy():
    """(here, {quadrant: pirates}) with None for quadrants out of scan range."""
    here, seen = None, {}
    for y in range(8):
        for x in range(8):
            col = 37 + 3 * x
            cell = r.screen.buffer[19 + y][col]
            if cell.reverse:
                here = (x, y)
            n = r.rows()[19 + y][col + 1]
            seen[(x, y)] = int(n) if n.isdigit() else (0 if n == "." else None)
    return here, seen


fights = 0
visited = set()
while r.elapsed() < SECONDS:
    if "Are you sure" in prompt():
        typed("y")
        continue
    here, seen = galaxy()
    if here is None:
        r.pump(0.5)
        continue
    visited.add(here)
    targets = pirates_here()
    if targets:
        fights += 1
        if fights % 2 == 0 and "Torpedoes" in r.text():
            r.key("t", 0.8)
            x, y = targets[0]
            typed(f"{x}{y}", 2.0)
            if "Torpedo 2" in prompt():
                typed("", 1.5)
        else:
            r.key("p", 0.8)
            for _ in targets:
                if "->" not in prompt():
                    break
                typed("500", 0.6)
            if "->" in prompt():
                typed("", 0.6)
            r.pump(1.8)
        continue
    # nearest quadrant with pirates, else the nearest one not scanned yet
    def dist(q):
        return max(abs(q[0] - here[0]), abs(q[1] - here[1]))
    hunt = [q for q, n in seen.items() if n and q != here]
    look = [q for q, n in seen.items() if n is None and q not in visited]
    pool = hunt or look or [q for q in seen if q != here]
    goal = min(pool, key=lambda q: (dist(q), random.random()))
    r.key("m", 0.8)
    typed(f"{goal[0]}{goal[1]}{random.randint(3, 6)}{random.randint(3, 6)}", 2.2)

r.pump(1.0)
r.finish(b"Q", grace=5.0)

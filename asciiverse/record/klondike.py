"""Records asciiverse/casts/klondike.cast: a deal played by a driver that
uses the game's own move hints. j cycles through the cards that can move
(the selected one has a * beside it) and the board marks where it can go:
s and a on the sorting stacks, f on the final piles. The driver plays to
a final pile whenever it can; otherwise it only makes moves that make
progress, the dealt card onto a stack or a run that uncovers a hidden
card, and deals a card (d) when nothing helps."""
from rec import Rec

SECONDS = 46
WL, WC = 22, 60
r = Rec("klondike", "Klondike")
r.wait_for("Klondike", 8)
r.pump(1.5)


def origin():
    rows = r.rows()
    top = next(y for y, l in enumerate(rows) if "Klondike" in l)
    left = rows[top].find("lqq")
    if left < 0:
        left = rows[top].find("┌")
    return top, left


def state():
    """(selected card's screen position or None, set of move marks)."""
    top, left = origin()
    buf = r.screen.buffer
    sel, marks = None, set()
    for y in range(top + 1, top + WL - 1):
        for x in range(left + 1, left + WC):    # the dealt card's * sits on the border
            ch = buf[y][x]
            if ch.data == "*":
                sel = (y, x - 2)
            elif ch.data in "saf" and ch.bold:   # the empty-pile checkerboard reads as a plain a
                marks.add(ch.data)
    return sel, marks


def on_final(sel):
    """A card on a final pile: the right column, window rows 10 to 19."""
    top, left = origin()
    return sel[1] == left + WC - 3 and sel[0] - top >= 10


def useful(sel):
    """The dealt card, or a stack card with a hidden card left of it."""
    top, left = origin()
    y, x = sel
    if x == left + WC - 3:                 # the dealt pile, right column, row 4
        return y - top == 4
    under = r.screen.buffer[y][x - 3].data if x - 3 > left else ""
    return under in ("l", "┌")


def turn():
    seen = []
    for _ in range(16):
        sel, marks = state()
        if sel is None or sel in seen:
            return False
        seen.append(sel)
        if on_final(sel):                  # never take a card back off a final pile
            r.key("j", 0.12)
            continue
        if "f" in marks:
            r.key("f", 0.45)
            return True
        if marks & {"s", "a"} and useful(sel):
            r.key(sorted(marks & {"s", "a"})[0], 0.45)
            return True
        r.key("j", 0.12)
    return False


while r.elapsed() < SECONDS:
    if "YOU WON" in r.text():
        r.pump(2.5)
        r.finish(b" ")
        break
    if not turn():
        r.key("d", 0.3)
else:
    r.pump(1.5)
    r.finish(b"q")

"""Records asciiverse/casts/gofish.cast: a game of Go Fish against the
computer. The driver reads its hand from the panel at the bottom (each
rank is a column, one row per card) and asks for a rank the computer has
asked for, since it must hold some, or else the rank it holds most of.
The computer plays its turns at once, so the driver pauses before each
ask to give the messages time to be read. A game still going at the end
is quit with x."""
import re

import pyte

from rec import Rec


# The message window scrolls with SU (CSI n S, "scroll up"), which pyte
# does not know; without it old lines stay on screen under new ones.
def _scroll_up(self, n=1, *rest, **kw):
    y = self.cursor.y
    self.cursor.y = self.margins.bottom if self.margins else self.lines - 1
    for _ in range(max(1, n)):
        self.index()
    self.cursor.y = y


pyte.Screen.scroll_up = _scroll_up
pyte.Stream.csi = dict(pyte.Stream.csi, S="scroll_up")

SECONDS = 54
r = Rec("gofish", "Go Fish")
r.wait_for("to start", 8)
r.pump(2.5)                     # the rules scroll by first


def hand():
    """{rank: count} from the panel, ranks as the game names them."""
    rows = r.rows()
    top = next(y for y in range(len(rows) - 4, len(rows)) if rows[y].startswith("Cards:"))
    first = rows[top][:60]
    out = {}
    for m in re.finditer(r"(10|[A2-9JQK])", first[7:]):
        col = 7 + m.start()
        name = m.group(1)
        out[name] = sum(1 for y in range(top, top + 3) if rows[y][col:col + len(name)] == name)
    return out


asked = set()                   # ranks asked since each was last worth asking
known = {}                      # rank: how many times the computer has asked for it


def computer_holds():
    """Ranks the computer asked for since we last asked for them."""
    out = set()
    for k in set(re.findall(r"I ask you for (10|[A2-9JQK])\.", r.text())):
        n = len(re.findall(r"I ask you for " + k + r"\.", r.text()))
        if n > known.get(k, 0):
            out.add(k)
    return out


def over():
    t = r.text()
    return "You win!!!" in t or "I win!!!" in t or "Tie!" in t


while r.elapsed() < SECONDS:
    if over():
        r.pump(3.0)
        r.finish(b" ")
        break
    r.pump(0.3)
    h = hand()
    if not h:
        continue
    wanted = [k for k in computer_holds() if k in h]
    fresh = [k for k in h if k not in asked] or list(h)
    if not [k for k in h if k not in asked]:
        asked.clear()
    ask = wanted[0] if wanted else max(fresh, key=lambda k: h[k])
    asked.add(ask)
    known[ask] = len(re.findall(r"I ask you for " + ask + r"\.", r.text()))
    r.pump(0.6)                 # time to read what just happened
    r.key(ask[0].lower(), 0.5)
else:
    r.pump(1.0)
    r.finish(b"x")

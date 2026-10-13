"""Records asciiverse/casts/battlestar.cast: from the stateroom to the hangar,
a launch, and a dogfight. The driver types the commands at a reading pace:
seven moves to the starfighter (the shortest way, found from loc.c), then
launch, then back, into the room where a Drenian fighter waits. In the
space window it steers by reading where the Drenian is: the arrow keys set
which way it drifts across the sight (it cannot be stopped), so the driver
keeps it within a column of the crosshair and fires as it crosses the
centre line. Then quit."""
import time

from rec import Rec

ROUTE = ["right", "right", "down", "right", "ahead", "right", "right"]
TOP, ROW, COL = 30 - 24, 12, 40      # fly.c: the 80x24 space window, its sight

r = Rec("battlestar", "Battlestar")
r.wait_for("stateroom")
r.pump(3.0)


def say(cmd, read=1.3):
    for ch in cmd:
        r.key(ch, 0.06)
    r.key(b"\r", read)


def drenian():
    """(line, column) of the Drenian's centre in the space window."""
    for y in range(TOP, 30):
        x = r.rows()[y].find("/-\\")
        if x >= 0:
            return y - TOP, x + 1
    return None


for step in ROUTE:
    say(step)
say("launch", 2.2)
say("back", 0.5)

# the dogfight
r.wait_for("TORPEDOES", 4)
dc = dr = 0
end = time.time() + 35
while time.time() < end and "TORPEDOES" in r.text():
    pos = drenian()
    if pos is None:
        r.pump(0.05)
        continue
    line, col = pos
    if line == ROW and abs(col - COL) < 2:
        r.key(" ", 0.2)                   # fire: the blast animates for ~1 s
        r.pump(1.5)
        continue
    if col < COL - 1 and dc != 1:
        r.key("l", 0.05); dc = 1
    elif col > COL + 1 and dc != -1:
        r.key("h", 0.05); dc = -1
    elif abs(col - COL) <= 1 and col == COL - 1 and dc == -1:
        r.key("l", 0.05); dc = 1          # swing back before it leaves the sight
    elif abs(col - COL) <= 1 and col == COL + 1 and dc == 1:
        r.key("h", 0.05); dc = -1
    if line < ROW and dr != 1:
        r.key("j", 0.05); dr = 1
    elif line > ROW and dr != -1:
        r.key("k", 0.05); dr = -1
    # wait for the Drenian's next move
    t = time.time()
    while time.time() - t < 0.6 and drenian() == pos:
        r.pump(0.03)

r.pump(3.0)
say("quit", 2.0)
r.finish(b"")

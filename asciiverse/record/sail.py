"""Records asciiverse/casts/sail.cast: Ambuscade vs. Baionnaise, in which
the British frigate starts upwind of the French corvette with room to
manoeuvre, played by a driver that reads the map. Turns come every seven
seconds of real time. Each turn it orders a move, closing on the
Baionnaise while she is far and then turning to bring her abeam, never
turning through the wind (that stops a square rigger), fires when she is
off a beam and in range (aiming at the hull), and reloads empty
broadsides with round shot. It quits with Q after SECONDS.

A ship on the map is two cells: its nation's letter at the bow (b for the
British Ambuscade, f for the French Baionnaise, upper case at full sail)
and a 0 at the stern, so the heading points from the 0 to the letter.
Headings are counted clockwise from up, and a left turn is one step
counter-clockwise, as in the manual's MOVEMENT section. The scenario's
wind blows from the south, heading 4."""
import math
import re

from rec import Rec, ENTER, DOWN

SECONDS = 52
WIND = 4                   # the wind comes from the south (dir_S)
STEPS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

r = Rec("sail", "Sail")
r.wait_for("Ranger vs. Drake")
r.pump(1.5)
for _ in range(6):         # the seventh scenario
    r.key(DOWN, 0.25)
r.pump(1.0)
r.key(ENTER, 1.5)          # and its first ship, the Ambuscade


def ships():
    """{"us" and "them": (row, col, heading)} for the ships on the map."""
    rows = r.rows()
    # pyte keeps curses' line drawing as letters, so find the map box by
    # its title line and the scenario name on its bottom edge
    top = next((i for i, l in enumerate(rows) if "Class" in l), None)
    if top is None:
        return {}
    out = {}
    for y in range(top + 1, len(rows)):
        if "vs." in rows[y]:
            break
        for x in range(11, 72):
            ch = rows[y][x]
            if not ch.isalpha():
                continue
            for h, (dy, dx) in enumerate(STEPS):
                yy, xx = y + dy, x + dx
                if top < yy < len(rows) and rows[yy][xx] == "0":
                    # the 0 is the stern: the ship heads the other way
                    out["us" if ch.lower() == "b" else "them"] = (y, x, (h + 4) % 8)
                    break
    return out


def turn_no():
    m = re.search(r"Turn\s+[-*]\s*(\d+)", r.text())
    return int(m.group(1)) if m else 0


def last_line():
    rows = r.rows()                 # messages end above the command line,
    top = next((i for i, l in enumerate(rows) if "Class" in l), 13)  # over the map
    lines = [l.strip() for l in rows[:top - 1] if l.strip()]
    return lines[-1] if lines else ""


def helm(h, target, ahead, drifting):
    """A move command turning from heading h to target the short way round
    unless that crosses the wind, at most two turns a move, then ahead."""
    d = (target - h) % 8
    right = [(h + i) % 8 for i in range(1, d + 1)]
    left = [(h - i) % 8 for i in range(1, 8 - d + 1)] if d else []
    if d == 0:
        turns = ""
    elif (d <= 4 and WIND not in right) or WIND in left:
        turns = "r" * min(d, 2)
    else:
        turns = "l" * min(8 - d, 2)
    if drifting and turns:
        return "1" + turns
    return turns + str(ahead)


def order(drifting, allowance):
    """The move for this turn, from where the two ships are. A drifting
    ship must move ahead before it turns."""
    s = ships()
    if "us" not in s or "them" not in s:
        return "1"
    ay, ax, h = s["us"]
    by, bx, _ = s["them"]
    dist = max(abs(by - ay), abs(bx - ax))
    bearing = round(math.degrees(math.atan2(bx - ax, ay - by)) / 45) % 8
    ahead = max(1, min(2, allowance))

    def nearest(options):
        options = [o % 8 for o in options if o % 8 != WIND]
        return min(options, key=lambda o: min((o - h) % 8, (h - o) % 8))

    if dist > 5:            # close in: point at her
        return helm(h, nearest([bearing, bearing + 1, bearing - 1]), ahead, drifting)
    if dist < 3:            # too close to fight: bear away
        return helm(h, nearest([bearing + 4, bearing + 3, bearing + 5]), ahead, drifting)
    # in range: bring her abeam, on whichever side is nearer
    return helm(h, nearest([bearing + 2, bearing - 2]), 1, drifting)


def abeam():
    """She is in range and off one of our beams."""
    s = ships()
    if "us" not in s or "them" not in s:
        return False
    ay, ax, h = s["us"]
    by, bx, _ = s["them"]
    bearing = round(math.degrees(math.atan2(bx - ax, ay - by)) / 45) % 8
    return max(abs(by - ay), abs(bx - ax)) <= 8 and (bearing - h) % 8 in (1, 2, 3, 5, 6, 7)


def answer_prompts(limit=6):
    for _ in range(limit):
        r.pump(0.6)
        t = last_line()
        if "hull or rigging" in t:
            r.key("h", 0.3)
        elif t.endswith("Fire?") or "Fire? " in t:
            r.key("y", 0.3)
        else:
            return


def reload():
    m = re.search(r"Load\s+(\S+)\s+(\S+)", r.text())
    if not m:
        return
    for side, state in zip("lr", m.groups()):
        if not state.startswith(("R", "D", "C", "G")):
            r.key("l", 0.5)
            r.key(side, 0.5)
            r.key("r", 0.8)


seen = turn_no()
while r.elapsed() < SECONDS:
    r.key("m", 0.8)
    m = re.search(r"move \((\d+), *('?)(\d+)\)", r.text())
    for ch in order(bool(m and m.group(2)), int(m.group(1)) if m else 1):
        r.key(ch, 0.12)
    r.key(ENTER, 0.8)
    if abeam():
        r.key("f", 0.6)
        answer_prompts()
    reload()
    # wait for the next turn
    while turn_no() == seen and r.elapsed() < SECONDS:
        r.pump(0.2)
    seen = turn_no()
    r.pump(0.8)

r.key("Q", 3.0)
r.finish(b" ", grace=8.0)

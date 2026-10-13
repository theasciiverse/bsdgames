"""Records asciiverse/casts/wump.cast: a game of Hunt the Wumpus typed by a
driver that reasons like a careful player. It maps the tunnels as it goes,
treats a room as safe once a neighbouring room was quiet, walks to the
nearest safe room it has not seen, and shoots once the smell narrows the
Wumpus down to one room next to it (not before 18 seconds, while there
is still safe cave to explore). The cave is random, so it plays up to
TAKES games and keeps the best take of 20 to 60 seconds: the first win,
or else the longest hunt."""
import re
from collections import deque

import os
import shutil

from rec import Rec, ENTER

ROOM = re.compile(r"You are in room (\d+)")
TUNNELS = re.compile(r"There are tunnels to rooms ([\d, and]+)\.")
WON = "slain the evil Wumpus"
OVER = ("dinners he's ever had", "Jules Verne", "EAT YOU", "eats you alive", "immediately ate you")


def play(r):
    """Plays one game; True when it ends in a win."""
    adj, visited, sniff, whoosh, missed = {}, set(), set(), set(), set()

    def look():
        """The room just described: (room, neighbours, warnings)."""
        text = r.text()
        block = text[text.rfind("You are in room"):]
        room = int(ROOM.search(block).group(1))
        nums = [int(n) for n in re.findall(r"\d+", TUNNELS.search(block.replace("\n", " ")).group(1))]
        return room, set(nums), ("*sniff*" in block, "*whoosh*" in block)

    def say(cmd):
        """Types a command; False once the game is over."""
        before = r.text().count("You are in room")
        for ch in cmd:
            r.key(ch, 0.11)
        r.key(ENTER, 0.1)
        for _ in range(80):
            t = r.text()
            if WON in t or any(o in t for o in OVER):
                return False
            if t.count("You are in room") > before or "Your bowstring" in t:
                break
            r.pump(0.05)
        # a reader's pause, a little longer after a warning (the cast's idle
        # limit is 2 s, so no pause is longer)
        block = r.text()[r.text().rfind("You are in room"):]
        r.pump(2.0 if "*" in block else 1.6)
        return True

    def safe(room, warned):
        """room was visited, or a visited neighbour of it was free of this warning."""
        return room in visited or any(room in adj[v] and v not in warned for v in visited)

    r.wait_for("ms?>")
    r.pump(1.5)
    while r.elapsed() < 52:
        room, near, (s, w) = look()
        if room not in visited:
            missed.clear()
        visited.add(room)
        adj[room] = near
        (sniff.add if s else sniff.discard)(room)
        (whoosh.add if w else whoosh.discard)(room)
        # where the Wumpus can be: next to every smelly room, never next to a quiet one
        cands = None
        for v in sniff:
            cands = set(adj[v]) if cands is None else cands & adj[v]
        cands = {c for c in (cands or set()) if not safe(c, sniff) and c not in missed}
        shot = sorted(cands & near) if s else []
        # the first 18 seconds go to exploring, so a quick win still shows the cave
        # late in a long hunt, take the best shot there is
        if len(shot) == 1 and r.elapsed() > 18 or shot and r.elapsed() > 42:
            missed.add(shot[0])
            if not say(f"s{shot[0]}"):
                return WON in r.text()
            continue
        # nearest unseen room safe from both, walking through known rooms
        prev = {room: None}
        q = deque([room])
        goal = None
        while q:
            p = q.popleft()
            if p not in visited:
                goal = p
                break
            for n in sorted(adj[p]):
                if n not in prev and safe(n, sniff) and safe(n, whoosh):
                    prev[n] = p
                    q.append(n)
        if goal is None:
            if shot:
                missed.add(shot[0])
                if not say(f"s{shot[0]}"):
                    return WON in r.text()
                continue
            # nothing known to be safe: the nearest unseen room the Wumpus
            # cannot be in (risking a pit), else any unseen room
            for ok in (lambda n: safe(n, sniff), lambda n: True):
                prev = {room: None}
                q = deque([room])
                while q and goal is None:
                    p = q.popleft()
                    for n in sorted(adj.get(p, ())):
                        if n in prev:
                            continue
                        if n not in visited and ok(n):
                            prev[n] = p
                            goal = n
                            break
                        if n in visited:
                            prev[n] = p
                            q.append(n)
                if goal is not None:
                    break
            if goal is None:
                return False
        while prev[goal] != room:
            goal = prev[goal]
        if not say(f"m{goal}"):
            return WON in r.text()
    return False


TAKES = 5
best = None                # (won, seconds, path) of the best take so far
for take in range(TAKES):
    r = Rec("wump", "Hunt the Wumpus")
    won = play(r)
    r.pump(3.0)
    r.finish(b"q\n" if not won else None)     # waits for the recorder to exit
    secs = r.elapsed()
    path = r.cast + f".take{take}"
    shutil.copy(r.cast, path)
    print(f"take {take + 1}: {'won' if won else 'lost'} in {secs:.0f} s", flush=True)
    if 20 <= secs <= 60 and (best is None or (won, secs) > best[:2]):
        best = (won, secs, path)
    if best and best[0]:
        break
if best:
    shutil.copy(best[2], r.cast)
    print(f"kept a {'win' if best[0] else 'loss'} of {best[1]:.0f} s", flush=True)
for take in range(TAKES):
    if os.path.exists(r.cast + f".take{take}"):
        os.remove(r.cast + f".take{take}")

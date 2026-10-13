"""Records asciiverse/casts/atc.cast: the Default arena. The driver reads the
radar (exits on the border, airports with their landing direction, planes
as a letter and an altitude) and the plane list (each plane's destination),
and after every update gives each plane its orders: planes for an exit
climb to 9000 feet and fly to the cell just inside it, then out through it
(a plane that has just come in keeps its heading until it is off the
border: flying along the border is leaving the airspace); planes for an airport go down to
2000 feet, fly to a point two cells short of the runway, turn onto its
heading and descend to land on it; planes waiting at an airport are cleared
to take off once the air near it is clear. The game updates every five
seconds, or at once on an empty command, which the driver sends about once a
second. atc's score table at the end shows the host's name, which the
driver replaces in the cast."""
import json, re, socket

from rec import Rec

# atc completes a command on a line feed; a carriage return is ignored
ENTER = b"\n"

SECONDS = 44
# compass keys for the eight headings (atc's directions, 0 = north)
KEYS = "wedcxzaq"
DXY = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
ARROW = {"^": 0, ">": 2, "v": 4, "<": 6}

r = Rec("atc", "ATC")
r.wait_for("Time:")
r.pump(0.5)


def radar_origin():
    """Screen row and column of arena cell (0, 0): the radar's top left."""
    for y, row in enumerate(r.rows()):
        if "Time:" in row:
            m = re.search(r"\d[q─-]", row)
            return y, m.start()
    return 0, 0


TOP, LEFT = radar_origin()
W, H = 30, 21


def cell(x, y):
    row = r.rows()[TOP + y]
    c = LEFT + 2 * x
    return row[c:c + 2]


def read_map():
    exits, airports = {}, {}
    for y in range(H):
        for x in range(W):
            s = cell(x, y)
            border = x in (0, W - 1) or y in (0, H - 1)
            if border and s[:1].isdigit():
                exits[int(s[0])] = (x, y)
            elif s[:1] in ARROW and s[1:2].isdigit():
                airports[int(s[1])] = (x, y, ARROW[s[0]])
    return exits, airports


def read_planes():
    """{name: (x, y, alt)} from the radar, {name: (alt, 'A' or 'E', n, text)}
    from the list."""
    pos = {}
    for y in range(H):
        for x in range(W):
            s = cell(x, y)
            if len(s) == 2 and s[0].isalpha() and s[1].isdigit():
                pos[s[0]] = (x, y, int(s[1]))
    info = {}
    for row in r.rows():
        for m in re.finditer(r"\b([A-Za-z])(\d)[ *]([AE])(\d):(.*?)(?=\s{2,}|$)", row[LEFT + 2 * W:]):
            info[m.group(1)] = (int(m.group(2)), m.group(3), int(m.group(4)), m.group(5))
    return pos, info


def clock():
    m = re.search(r"Time:\s*(\d+)", r.text())
    return int(m.group(1)) if m else 0


def toward(x, y, tx, ty):
    dx = (tx > x) - (tx < x)
    dy = (ty > y) - (ty < y)
    return DXY.index((dx, dy)) if (dx or dy) else None


def order(p, keys):
    r.key(p.lower(), 0.03)          # atc reads plane names in lower case only
    for k in keys:
        r.key(k, 0.03)
    r.key(ENTER, 0.08)


EXITS, AIRPORTS = {}, {}
seen = clock()
while r.elapsed() < SECONDS:
    exits, airports = read_map()     # a plane can hide an exit's number: merge
    EXITS.update(exits)
    AIRPORTS.update(airports)
    pos, info = read_planes()
    for p, (alt, kind, n, text) in sorted(info.items()):
        here = pos.get(p)
        if kind == "E":
            if here is None:                          # waiting at an airport
                if not any(qa <= 2 for qx, qy, qa in pos.values()):
                    order(p, "a9")
                continue
            x, y, a = here
            if a < 9:
                order(p, "a9")
            if x in (0, W - 1) or y in (0, H - 1) or n not in EXITS:
                continue                              # just in: keep flying inwards
            ex, ey = EXITS[n]
            gx, gy = min(max(ex, 1), W - 2), min(max(ey, 1), H - 2)
            if (x, y) == (gx, gy):
                order(p, "tte" + str(n))              # out through the exit
            else:
                h = toward(x, y, gx, gy)
                order(p, "t" + KEYS[h])
        elif n in AIRPORTS and here:
            ax, ay, d = AIRPORTS[n]
            px, py = ax - 2 * DXY[d][0], ay - 2 * DXY[d][1]
            x, y, a = here
            if x in (0, W - 1) or y in (0, H - 1):
                if a != 2:
                    order(p, "a2")
                continue
            if (x, y) == (px, py):
                order(p, "t" + KEYS[d])
                order(p, "a0")
            elif (x, y) == (ax - DXY[d][0], ay - DXY[d][1]):
                pass                                    # on final, already descending
            else:
                h = toward(x, y, px, py)
                if h is not None:
                    order(p, "t" + KEYS[h])
                if a != 2:
                    order(p, "a2")
    # an empty command runs the next update now, instead of after 5 s
    r.pump(0.35)
    if clock() == seen:
        r.key(" ", 0.1)            # an empty command: run the next update
    for _ in range(50):
        if clock() != seen or "Hit space" in r.text():
            break
        r.pump(0.1)
    if "Hit space" in r.text():
        break
    seen = clock()
    r.pump(0.15)

r.finish(b"Q\n")


def hide_host(cast):
    """atc's score table, printed when it quits, shows the host's name; put a
    neutral word of the same length in its place so the columns stay put."""
    host = socket.gethostname()
    if not host:
        return
    word = ("asciiverse" * 4)[:len(host)]
    lines = open(cast).read().splitlines()
    out = [lines[0]]
    for line in lines[1:]:
        e = json.loads(line)
        if e[1] == "o":
            e[2] = e[2].replace(host, word)
        out.append(json.dumps(e, ensure_ascii=False))
    open(cast, "w").write("\n".join(out) + "\n")


hide_host(r.cast)

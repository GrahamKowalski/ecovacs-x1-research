"""Extract small, sanitized test fixtures from a x1_pc_stream_rx .raw capture.

Picks one /robot/Robot message per attachment/charge case (LDS scan points stripped,
so no room geometry leaves the capture), plus /task/WorkState and /map/ChargerDockInfo
messages per state. PC side, Python 3.

    python x1_extract_fixtures.py <capture.raw> <defs-dir> <outdir>
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosmsg_decode as rd

raw, defsdir, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)

def load(t):
    text = open(os.path.join(defsdir, t + ".msg"), encoding="utf-8").read().split("\n", 1)[1]
    return rd.parse_definition(text, t)

SPECS = {"/robot/Robot": ("robot/Robot", load("robot/Robot")),
         "/task/WorkState": ("task/WorkState", load("task/WorkState")),
         "/map/ChargerDockInfo": ("map/ChargerDockInfo", load("map/ChargerDockInfo"))}

def strip_lds(buf, msg):
    """Rewrite a robot/Robot body with ldsPic.points = [] (points are the last variable array)."""
    # ldsPic = Header, LdsPoint[] points, PredictPose ldsPose. Re-encode the tail.
    n = len(msg["ldsPic"]["points"])
    # find offset of the points count: decode up to ldsPic header via the spec cursor
    spec = SPECS["/robot/Robot"][1]
    cur = rd.Cursor(buf)
    rd._decode_msg(cur, {k: v for k, v in spec.items()}, "robot/Robot") if False else None
    # simpler: locate by structure: the tail is  [u32 n][n*20 bytes][ldsPose 56 bytes]
    tail = 4 + n * 20 + 2 * (16 + 12)  # ldsPose: two Pose = header(16, empty frame_id) + 12
    head = len(buf) - tail
    assert struct.unpack_from("<I", buf, head)[0] == n, "lds point count mismatch"
    return buf[:head] + struct.pack("<I", 0) + buf[head + 4 + n * 20:]

wanted = {
    "robot_vacuum_module_off_dock": lambda m: m["waterbox"][0]["value"] == 4 and m["chargestate"]["isOnCharger"] == 0 and m["dirtbox"][0]["value"] == 0,
    "robot_dustbin_out": lambda m: m["dirtbox"][0]["value"] == 1,
    "robot_no_module": lambda m: m["waterbox"][0]["value"] == 0,
    "robot_mop_plate": lambda m: m["waterbox"][0]["value"] == 2 and m["carpet"][0]["value"] == 0,
    "robot_mop_plate_on_carpet": lambda m: m["waterbox"][0]["value"] == 2 and m["carpet"][0]["value"] == 1,
    "robot_on_charger": lambda m: m["chargestate"]["isOnCharger"] == 1,
    "workstate_idle": lambda m: m["worktype"] == 7 and m["state"] == 0,
    "workstate_relocating": lambda m: m["worktype"] == 8 and m["state"] == 1,
    "workstate_auto_clean_running": lambda m: m["worktype"] == 0 and m["state"] == 1,
    "workstate_auto_clean_paused": lambda m: m["worktype"] == 0 and m["state"] == 2,
    "dockinfo_found": lambda m: m["hasfindDock"] == 1,
    "dockinfo_get": lambda m: m["hasfindDock"] == 0 and m["info"] == 3,
}
found = {}
with open(raw, "rb") as f:
    while True:
        h = f.read(4)
        if len(h) < 4:
            break
        body = f.read(struct.unpack("<I", h)[0])
        ts, kind, tlen = struct.unpack_from("<dBH", body, 0)
        topic = body[11:11 + tlen].decode()
        if kind != 1 or topic not in SPECS:
            continue
        payload = body[11 + tlen:]
        ttype, spec = SPECS[topic]
        msg, used = rd.decode(payload, spec, ttype)
        for name, pred in wanted.items():
            if name in found:
                continue
            prefix = name.split("_")[0]
            if (prefix == "robot") != (topic == "/robot/Robot"):
                continue
            if prefix == "workstate" and topic != "/task/WorkState":
                continue
            if prefix == "dockinfo" and topic != "/map/ChargerDockInfo":
                continue
            try:
                if pred(msg):
                    out = strip_lds(payload, msg) if topic == "/robot/Robot" else payload
                    found[name] = (topic, len(out))
                    open(os.path.join(outdir, name + ".bin"), "wb").write(out)
            except (KeyError, IndexError):
                pass
for k, v in sorted(found.items()):
    print("%-32s %s %d bytes" % (k, v[0], v[1]))
print("missing:", sorted(set(wanted) - set(found)))

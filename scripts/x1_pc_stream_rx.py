"""PC-side receiver for x1_stream.py. Connects to the robot, decodes every message
with the publisher-supplied message_definition (fallback: rootfs python modules),
and prints only the fields that CHANGED, with timestamps. Everything printed also
goes to a log; raw frames of changed messages go to a .raw file for replay.

    python x1_pc_stream_rx.py <robot-ip> <port> <logdir> [--defs <site-packages>]
                              [--ignore <regex>] [--show-all <topic>]

While running, type a note and press Enter to stamp it into the log
(e.g. "mop removed"). Ctrl-C to stop.
"""
import argparse
import os
import re
import socket
import struct
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosmsg_decode as rd  # noqa: E402

# motor currents (currents.*) flicker by 1-2 ADC counts at 50 Hz, so they are hidden by default
DEFAULT_IGNORE = r"^(ldsPic\.|rangeDetects\.|currents\.|.*\.header\.|header\.|pose\.predictPose\.)"

ap = argparse.ArgumentParser()
ap.add_argument("host")
ap.add_argument("port", type=int)
ap.add_argument("logdir")
ap.add_argument("--defs", help="rootfs site-packages dir for definition fallback")
ap.add_argument("--ignore", default=DEFAULT_IGNORE, help="regex of flattened field names to hide from diffs")
ap.add_argument("--show-all", action="append", default=[], help="topic whose full message is printed every time")
ap.add_argument("--pose-every", type=float, default=5.0, help="seconds between pose/battery heartbeat lines")
ap.add_argument("--once", type=float, default=0, help="exit after this many seconds (0 = run until Ctrl-C)")
ap.add_argument("--mute", action="append", default=[], help="topic to record to .raw but not print (e.g. /task/omnireport)")
a = ap.parse_args()

os.makedirs(a.logdir, exist_ok=True)
stamp = time.strftime("%Y%m%d_%H%M%S")
log = open(os.path.join(a.logdir, "stream_%s.log" % stamp), "a", encoding="utf-8")
raw = open(os.path.join(a.logdir, "stream_%s.raw" % stamp), "ab")
ignore = re.compile(a.ignore)
local_defs = rd.load_local_definitions(a.defs) if a.defs else {}
started = time.time()


def out(line):
    t = time.strftime("%H:%M:%S") + ".%03d" % int((time.time() % 1) * 1000)
    s = "%s %s" % (t, line)
    print(s, flush=True)
    log.write(s + "\n")
    log.flush()


def stdin_notes():
    for line in sys.stdin:
        line = line.strip()
        if line:
            out("### NOTE: " + line)


threading.Thread(target=stdin_notes, daemon=True).start()

specs = {}   # topic -> (type, specs)
last = {}    # topic -> flattened visible dict
count = {}   # topic -> messages seen
last_hb = [0.0]


def fmt(v):
    if isinstance(v, bytes):
        return v.hex() if len(v) <= 32 else "%d bytes" % len(v)
    if isinstance(v, float):
        return "%.4f" % v
    return repr(v)


def write_raw(ts, topic, payload):
    t = topic.encode()
    body = struct.pack("<dBH", ts, 1, len(t)) + t + payload
    raw.write(struct.pack("<I", len(body)) + body)
    raw.flush()


def handle(ts, kind, topic, payload):
    if kind == 2:
        out("[robot] %s: %s" % (topic, payload.decode("utf-8", "replace")))
        return
    if kind == 0:
        h = rd.parse_tcpros_header(payload)
        ttype = h.get("type", "?")
        text = h.get("message_definition") or local_defs.get(ttype)
        if not text:
            out("[hdr] %s type=%s: NO DEFINITION (not in header, not local)" % (topic, ttype))
            return
        specs[topic] = (ttype, rd.parse_definition(text, ttype))
        out("[hdr] %s type=%s md5=%s def=%s" % (
            topic, ttype, h.get("md5sum", "?")[:8],
            "from publisher" if h.get("message_definition") else "local fallback"))
        return
    if topic not in specs:
        return
    ttype, sp = specs[topic]
    try:
        msg, used = rd.decode(payload, sp, ttype)
    except Exception as e:
        out("[err] %s decode failed: %r (%d bytes)" % (topic, e, len(payload)))
        write_raw(ts, topic, payload)
        return
    if used != len(payload):
        out("[warn] %s consumed %d of %d bytes" % (topic, used, len(payload)))
    flat = rd.flatten(msg)
    count[topic] = count.get(topic, 0) + 1
    prev = last.get(topic)
    vis = {k: v for k, v in flat.items() if not ignore.search(k)}
    changed = []
    if prev is None or topic in a.show_all:
        changed = [(k, None, v) for k, v in vis.items()]
    else:
        for k, v in vis.items():
            if prev.get(k) != v:
                changed.append((k, prev.get(k), v))
        for k in prev:
            if k not in vis:
                changed.append((k, prev[k], "<gone>"))
    last[topic] = vis
    if changed:
        if topic not in a.mute:
            head = "FIRST" if prev is None else "CHANGED"
            out("%s %s (#%d, %d bytes)" % (head, topic, count[topic], len(payload)))
            for k, o, n in changed:
                out("    %-40s %s" % (k, fmt(n) if o is None else "%s -> %s" % (fmt(o), fmt(n))))
        write_raw(ts, topic, payload)
    if topic == "/robot/Robot" and time.time() - last_hb[0] > a.pose_every:
        last_hb[0] = time.time()
        p = msg["pose"]["pose"]
        out("[hb] pose x=%.0f y=%.0f th=%.3f bat=%d%% charger=%d/%d (#%d)" % (
            p["x"], p["y"], p["theta"], msg["battery"]["battery"],
            msg["chargestate"]["isOnCharger"], msg["chargestate"]["chargeState"], count[topic]))


def readn(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            raise EOFError
        b += c
    return b


while True:
    try:
        s = socket.create_connection((a.host, a.port), timeout=5)
        s.settimeout(5)
        out("connected to %s:%d (log %s)" % (a.host, a.port, log.name))
        while True:
            if a.once and time.time() - started > a.once:
                out("time limit reached, stopping")
                sys.exit(0)
            try:
                n = struct.unpack("<I", readn(s, 4))[0]
            except socket.timeout:
                continue
            body = readn(s, n)
            ts, kind, tlen = struct.unpack_from("<dBH", body, 0)
            topic = body[11:11 + tlen].decode()
            handle(ts, kind, topic, body[11 + tlen:])
    except KeyboardInterrupt:
        out("stopped")
        break
    except (OSError, EOFError) as e:
        if a.once and time.time() - started > a.once:
            out("time limit reached, stopping")
            break
        out("connection lost (%r), retrying in 2s" % (e,))
        time.sleep(2)

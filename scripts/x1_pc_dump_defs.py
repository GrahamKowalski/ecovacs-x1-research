"""Save the message definitions the robot's publishers send in their TCPROS headers.
Connects to a running x1_stream.py (which replays every cached header on connect),
collects the kind-0 frames for a few seconds, and writes one <pkg>/<Name>.msg
text file per topic type. PC side, Python 3.

    python x1_pc_dump_defs.py <robot-ip> <port> <outdir> [seconds=8]
"""
import os
import socket
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosmsg_decode as rd  # noqa: E402

host, port, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
secs = float(sys.argv[4]) if len(sys.argv) > 4 else 8.0


def readn(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            raise EOFError
        b += c
    return b


s = socket.create_connection((host, port), timeout=5)
s.settimeout(15)
deadline = time.time() + secs
seen = {}
while time.time() < deadline:
    try:
        n = struct.unpack("<I", readn(s, 4))[0]
    except socket.timeout:
        continue
    body = readn(s, n)
    ts, kind, tlen = struct.unpack_from("<dBH", body, 0)
    if kind != 0:
        continue
    topic = body[11:11 + tlen].decode()
    h = rd.parse_tcpros_header(body[11 + tlen:])
    ttype, text = h.get("type"), h.get("message_definition")
    if not ttype or not text or ttype in seen:
        continue
    seen[ttype] = topic
    path = os.path.join(outdir, ttype + ".msg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# topic %s, md5 %s\n" % (topic, h.get("md5sum", "?")))
        f.write(text)
s.close()
for t in sorted(seen):
    print("%-35s %s" % (t, seen[t]))
print("%d definitions -> %s" % (len(seen), outdir))

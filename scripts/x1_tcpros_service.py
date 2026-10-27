import socket, struct, sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc

service = sys.argv[1]
md5 = sys.argv[2]
t = int(sys.argv[3]) if len(sys.argv) > 3 else 0
mapid = int(sys.argv[4]) if len(sys.argv) > 4 else 0
out = sys.argv[5] if len(sys.argv) > 5 else "/tmp/showmap_live.bin"
caller = "/valetudo_mapfetch"

code, msg, uri = xc.ServerProxy("http://127.0.0.1:11311").lookupService(caller, service)
if code != 1:
    sys.stderr.write("lookupService failed: %s\n" % msg); sys.exit(1)
host, port = uri[len("rosrpc://"):].rsplit(":", 1)
s = socket.create_connection((host, int(port)), timeout=10)

def enc(fields):
    body = b""
    for k, v in fields.items():
        kv = ("%s=%s" % (k, v)).encode()
        body += struct.pack("<I", len(kv)) + kv
    return struct.pack("<I", len(body)) + body

def readn(n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            break
        b += c
    return b

s.sendall(enc({"callerid": caller, "service": service, "md5sum": md5, "persistent": "0"}))
server_hdr = readn(struct.unpack("<I", readn(4))[0])
s.sendall(struct.pack("<I", 5) + struct.pack("<BI", t, mapid))
ok = readn(1)
if not ok:
    sys.stderr.write("no response; server header=%r\n" % server_hdr[:160]); sys.exit(2)
okv = bytearray(ok)[0]
blen = struct.unpack("<I", readn(4))[0]
payload = readn(blen)
s.close()
if okv == 1:
    f = open(out, "wb"); f.write(payload); f.close()
    sys.stderr.write("OK ok=1 payload=%d -> %s\n" % (len(payload), out))
else:
    sys.stderr.write("CALL ERROR ok=%d msg=%r\n" % (okv, payload[:200]))

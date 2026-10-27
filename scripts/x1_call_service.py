# Runs ON THE ROBOT with python2 (needs /tmp/rosmsg_decode.py next to it).
# Generic ROS service client over raw TCPROS.
#
#   python2 x1_call_service.py probe <service> [md5]
#       Connect, exchange headers only, print the server's header. With md5 "*" (default)
#       the server reports its types; with a wrong md5 it refuses and the error text
#       names the md5 it expects. Harmless: no request is sent.
#
#   python2 x1_call_service.py call <service> <req.msg> <resp.msg> '<json>' [md5]
#       Encode the JSON request with the definition in <req.msg> (first line may be a
#       "# topic ..." comment), send it, decode the response with <resp.msg>.
#       md5 defaults to the computed service md5; pass '*' to skip the check.
#
#   python2 x1_call_service.py raw <service> <hex request bytes> [md5]
#       Send the bytes as-is, print the ok flag and the response as hex. A
#       "Buffer Overrun" error means the server wanted more bytes than were sent.
#
# Request/response .msg files: first non-comment section is the type; nested sections
# as usual. The type name is taken from the file path (<pkg>/<Name>.msg) or "x/Req".
import json, os, socket, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosmsg_decode as rd
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc

CALLER = "/valetudo_srv"
NL = chr(10)


def enc_header(fields):
    body = b""
    for k, v in fields.items():
        kv = ("%s=%s" % (k, v)).encode()
        body += struct.pack("<I", len(kv)) + kv
    return struct.pack("<I", len(body)) + body


def readn(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            raise EOFError("server closed")
        b += c
    return b


def connect(service):
    code, msg, uri = xc.ServerProxy("http://127.0.0.1:11311").lookupService(CALLER, service)
    if code != 1:
        sys.stderr.write("lookupService failed: %s%s" % (msg, NL))
        sys.exit(1)
    host, port = uri[len("rosrpc://"):].rsplit(":", 1)
    return socket.create_connection((host, int(port)), timeout=15)


def load_def(path, fallback_type):
    text = open(path).read()
    if text.startswith("#"):
        text = text.split(NL, 1)[1]
    parts = path.replace(chr(92), "/").split("/")
    t = "%s/%s" % (parts[-2], parts[-1][:-4]) if len(parts) >= 2 and path.endswith(".msg") else fallback_type
    return t, rd.parse_definition(text, t)


def exchange(service, md5, req):
    """Header exchange + one request. Returns (ok, response_bytes)."""
    s = connect(service)
    s.sendall(enc_header({"callerid": CALLER, "service": service, "md5sum": md5, "persistent": "0"}))
    hdr = rd.parse_tcpros_header(readn(s, struct.unpack("<I", readn(s, 4))[0]))
    if "error" in hdr:
        sys.stderr.write("server refused: %s%s" % (hdr["error"], NL))
        sys.exit(2)
    s.sendall(struct.pack("<I", len(req)) + req)
    ok = bytearray(readn(s, 1))[0]
    resp = readn(s, struct.unpack("<I", readn(s, 4))[0])
    s.close()
    return ok, resp


mode = sys.argv[1]
service = sys.argv[2]

if mode == "probe":
    s = connect(service)
    s.sendall(enc_header({"callerid": CALLER, "service": service, "md5sum": sys.argv[3] if len(sys.argv) > 3 else "*", "probe": "1"}))
    hdr = readn(s, struct.unpack("<I", readn(s, 4))[0])
    s.close()
    for k, v in sorted(rd.parse_tcpros_header(hdr).items()):
        sys.stdout.write("%s=%s%s" % (k, v, NL))
    sys.exit(0)

if mode == "call":
    req_path, resp_path, body_json = sys.argv[3], sys.argv[4], sys.argv[5]
    req_t, req_specs = load_def(req_path, "x/Request")
    resp_t, resp_specs = load_def(resp_path, "x/Response")
    md5 = sys.argv[6] if len(sys.argv) > 6 else rd.service_md5(req_specs, req_t, resp_specs, resp_t)
    req = rd.encode(json.loads(body_json), req_specs, req_t)
    ok, resp = exchange(service, md5, req)
    if ok != 1:
        sys.stderr.write("CALL ERROR: %r%s" % (resp[:200], NL))
        sys.exit(3)
    msg, used = rd.decode(resp, resp_specs, resp_t)
    sys.stdout.write(json.dumps(msg, default=lambda o: list(bytearray(o)) if isinstance(o, (bytes, bytearray)) else str(o)) + NL)
    sys.exit(0)

if mode == "raw":
    req = bytes(bytearray.fromhex(sys.argv[3]))
    md5 = sys.argv[4] if len(sys.argv) > 4 else "*"
    ok, resp = exchange(service, md5, req)
    shown = "".join("%02x" % b for b in bytearray(resp)) if ok == 1 else repr(resp[:120])
    sys.stdout.write("len=%d ok=%d resp=%s%s" % (len(req), ok, shown, NL))
    sys.exit(0 if ok == 1 else 3)

sys.stderr.write("usage: probe <service> [md5] | call <service> <req.msg> <resp.msg> '<json>' [md5] | raw <service> <hex> [md5]" + NL)
sys.exit(1)

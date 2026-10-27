import socket, struct, sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc

MASTER = "http://127.0.0.1:11311"
TOPIC = "/robot/Robot"
TYPE = "robot/Robot"
CALLER = "/valetudo_posefetch"

m = xc.ServerProxy(MASTER)
state = m.getSystemState(CALLER)[2]
pubs = dict(state[0])
nodes = pubs.get(TOPIC)
if not nodes:
    sys.stderr.write("no publisher for %s\n" % TOPIC); sys.exit(1)
nodeuri = m.lookupNode(CALLER, nodes[0])[2]
proto = xc.ServerProxy(nodeuri).requestTopic(CALLER, TOPIC, [["TCPROS"]])[2]
host, port = proto[1], proto[2]
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

s.sendall(enc({"callerid": CALLER, "topic": TOPIC, "md5sum": "*", "type": TYPE, "tcp_nodelay": "1"}))
readn(struct.unpack("<I", readn(4))[0])          # publisher header
data = readn(struct.unpack("<I", readn(4))[0])   # one Robot message
s.close()
open("/tmp/robot_msg.bin", "wb").write(data)

o = [0]
def rd(fmt):
    v = struct.unpack_from("<" + fmt, data, o[0]); o[0] += struct.calcsize("<" + fmt); return v
def skiphdr():
    rd("III"); L = rd("I")[0]; o[0] += L   # seq, sec, nsec, frame_id
skiphdr()                 # Robot.header
skiphdr(); rd("fff")      # PredictPose.predictPose
skiphdr(); x, y, th = rd("fff")   # PredictPose.pose (current)
sys.stderr.write("robot pose x=%.4f y=%.4f theta=%.4f (msg %d bytes)\n" % (x, y, th, len(data)))

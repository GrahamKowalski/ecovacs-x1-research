# Runs ON THE ROBOT (python2). Publishes a single message to a ROS topic the robot
# subscribes to, by acting as a real (temporary) TCPROS publisher. It first subscribes
# once to the topic to steal the existing publisher's md5sum + message_definition, then
# advertises with the same and serves the payload to any subscriber that connects.
#
#   python2 x1_publish.py <topic> <payload_hex> [seconds]
import socket, struct, sys, threading, time, os
try:
    import xmlrpclib as xc
    from SimpleXMLRPCServer import SimpleXMLRPCServer
except ImportError:
    import xmlrpc.client as xc
    from xmlrpc.server import SimpleXMLRPCServer

MASTER = "http://127.0.0.1:11311"
CALLER = "/valetudo_pub"
HOST = "127.0.0.1"
topic = sys.argv[1]
payload = bytes(bytearray.fromhex(sys.argv[2]))
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0

def enc(fields):
    b = b""
    for k, v in fields.items():
        kv = ("%s=%s" % (k, v)).encode()
        b += struct.pack("<I", len(kv)) + kv
    return struct.pack("<I", len(b)) + b

def readn(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            raise EOFError()
        b += c
    return b

def parse_hdr(raw):
    f = {}; o = 0
    while o + 4 <= len(raw):
        n = struct.unpack("<I", raw[o:o+4])[0]
        o += 4; kv = raw[o:o+n]; o += n
        k, _, v = kv.partition(b"=")
        f[k.decode()] = v
    return f

# 1. subscribe once to grab the publisher's header (type, md5, definition)
m = xc.ServerProxy(MASTER)
ttype = dict(m.getTopicTypes(CALLER)[2]).get(topic)
pubs = dict(m.getSystemState(CALLER)[2][0]).get(topic)
if not ttype or not pubs:
    sys.stderr.write("no type/publisher for %s\n" % topic); sys.exit(1)
uri = m.lookupNode(CALLER, pubs[0])[2]
proto = xc.ServerProxy(uri).requestTopic(CALLER, topic, [["TCPROS"]])[2]
s = socket.create_connection((proto[1], int(proto[2])), timeout=10)
s.sendall(enc({"callerid": CALLER + "_probe", "topic": topic, "md5sum": "*", "type": ttype, "tcp_nodelay": "1"}))
hdr = parse_hdr(readn(s, struct.unpack("<I", readn(s, 4))[0]))
s.close()
md5 = hdr.get("md5sum", b"*").decode()
mdef = hdr.get("message_definition", b"").decode("latin1")
sys.stderr.write("topic %s type %s md5 %s\n" % (topic, ttype, md5))

# 2. TCPROS server that serves the payload
srv_sock = socket.socket(); srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv_sock.bind((HOST, 0)); srv_sock.listen(5)
tcpport = srv_sock.getsockname()[1]
nconn = [0]
def tcp_loop():
    while True:
        try:
            c, a = srv_sock.accept()
        except Exception:
            return
        try:
            n = struct.unpack("<I", readn(c, 4))[0]; readn(c, n)   # subscriber header
            c.sendall(enc({"callerid": CALLER, "topic": topic, "type": ttype,
                           "md5sum": md5, "message_definition": mdef, "latching": "1", "tcp_nodelay": "1"}))
            c.sendall(struct.pack("<I", len(payload)) + payload)
            nconn[0] += 1
            sys.stderr.write("served payload to %s\n" % (a,))
        except Exception as e:
            sys.stderr.write("tcp err %r\n" % e)
t = threading.Thread(target=tcp_loop); t.daemon = True; t.start()

# 3. XMLRPC node API so subscribers can requestTopic us
class Node:
    def requestTopic(self, caller, t, protos):
        return [1, "", ["TCPROS", HOST, tcpport]]
    def getPid(self, caller):
        return [1, "", os.getpid()]
    def publisherUpdate(self, *a):
        return [1, "", 0]
    def getBusInfo(self, caller):
        return [1, "", []]
    def getSubscriptions(self, caller):
        return [1, "", []]
    def getPublications(self, caller):
        return [1, "", [[topic, ttype]]]
    def shutdown(self, *a):
        return [1, "", 0]
rpc = SimpleXMLRPCServer((HOST, 0), logRequests=False, allow_none=True)
rpc.register_instance(Node(), allow_dotted_names=False)
myport = rpc.server_address[1]
rt = threading.Thread(target=rpc.serve_forever); rt.daemon = True; rt.start()
myuri = "http://%s:%d/" % (HOST, myport)

# 4. register as publisher; master notifies subscribers who then connect to us
code, msg, subs = m.registerPublisher(CALLER, topic, ttype, myuri)
sys.stderr.write("registered publisher, current subscribers: %s\n" % (subs,))
time.sleep(secs)
try:
    m.unregisterPublisher(CALLER, topic, myuri)
except Exception:
    pass
sys.stderr.write("done, connections served: %d\n" % nconn[0])

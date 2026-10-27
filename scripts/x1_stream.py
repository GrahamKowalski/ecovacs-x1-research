# Runs ON THE ROBOT with python2 (stdlib only). Subscribes to several ROS topics
# over raw TCPROS and streams every message to all connected PC clients as
# length-framed records. Read-only: it never publishes or calls services.
#
#   python2 /tmp/x1_stream.py <listen_port> <topic> [<topic> ...]
#
# Frame: <I total><d unix_ts><B kind><H tlen><topic><payload>
#   kind 0 = publisher TCPROS header body (has type, md5sum, message_definition)
#   kind 1 = raw message body
#   kind 2 = text note from the robot side (e.g. "no publisher for X")
import socket, struct, sys, threading, time
try:
    import xmlrpclib as xc
    import Queue as queue
except ImportError:
    import xmlrpc.client as xc
    import queue

MASTER = "http://127.0.0.1:11311"
CALLER = "/valetudo_stream"
port = int(sys.argv[1])
topics = sys.argv[2:]
hdr_cache = {}
clients = []            # per-client outbound queues
clients_lock = threading.Lock()


def frame(kind, topic, payload):
    t = topic.encode()
    body = struct.pack("<dBH", time.time(), kind, len(t)) + t + payload
    return struct.pack("<I", len(body)) + body


def broadcast(f):
    with clients_lock:
        cs = list(clients)
    for cq in cs:
        try:
            cq.put_nowait(f)
        except queue.Full:
            pass  # drop for a slow client rather than stall the robot side


def enc(fields):
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
            raise EOFError("publisher closed")
        b += c
    return b


def note(topic, text):
    sys.stderr.write("%s: %s\n" % (topic, text))
    broadcast(frame(2, topic, text.encode()))


def subscribe(topic, ttype):
    m = xc.ServerProxy(MASTER)
    while True:
        try:
            pubs = dict(m.getSystemState(CALLER)[2][0]).get(topic)
            if not pubs:
                # A node can restart (crash recovery), so keep retrying rather than
                # exiting the thread; the publisher usually returns within seconds.
                note(topic, "no publisher, retrying in 3s")
                time.sleep(3)
                continue
            uri = m.lookupNode(CALLER, pubs[0])[2]
            proto = xc.ServerProxy(uri).requestTopic(CALLER, topic, [["TCPROS"]])[2]
            s = socket.create_connection((proto[1], int(proto[2])), timeout=30)
            s.sendall(enc({"callerid": CALLER, "topic": topic, "md5sum": "*",
                           "type": ttype, "tcp_nodelay": "1"}))
            hdr = readn(s, struct.unpack("<I", readn(s, 4))[0])
            hdr_cache[topic] = frame(0, topic, hdr)
            broadcast(hdr_cache[topic])
            s.settimeout(None)
            while True:
                data = readn(s, struct.unpack("<I", readn(s, 4))[0])
                broadcast(frame(1, topic, data))
        except Exception as e:
            note(topic, "subscribe error %r, retrying in 3s" % (e,))
            time.sleep(3)


def serve_client(c, addr):
    cq = queue.Queue(maxsize=1000)
    with clients_lock:
        clients.append(cq)
    try:
        # publishers send their header once, so replay cached headers to each new client
        for f in list(hdr_cache.values()):
            c.sendall(f)
        while True:
            c.sendall(cq.get())
    except Exception as e:
        sys.stderr.write("client %s gone: %r\n" % (addr, e))
    finally:
        with clients_lock:
            clients.remove(cq)
        c.close()


m = xc.ServerProxy(MASTER)
types = dict(m.getTopicTypes(CALLER)[2])
for t in topics:
    ttype = types.get(t)
    if not ttype:
        note(t, "unknown topic (not in master's type table)")
        continue
    th = threading.Thread(target=subscribe, args=(t, ttype))
    th.daemon = True
    th.start()

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", port))
srv.listen(4)
sys.stderr.write("listening on %d for %d topics\n" % (port, len(topics)))
while True:
    c, addr = srv.accept()
    sys.stderr.write("client %s\n" % (addr,))
    th = threading.Thread(target=serve_client, args=(c, addr))
    th.daemon = True
    th.start()

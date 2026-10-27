import socket, struct, sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc
MASTER="http://127.0.0.1:11311"; CALLER="/valetudo_slammeta"
TOPIC = sys.argv[1] if len(sys.argv) > 1 else "/slam/SlamMap"
TYPE = sys.argv[2] if len(sys.argv) > 2 else "slam/SlamMap"
m = xc.ServerProxy(MASTER)
pubs = dict(m.getSystemState(CALLER)[2][0])
nodes = pubs.get(TOPIC)
if not nodes:
    sys.stderr.write("no publisher for %s\n" % TOPIC); sys.exit(1)
nodeuri = m.lookupNode(CALLER, nodes[0])[2]
proto = xc.ServerProxy(nodeuri).requestTopic(CALLER, TOPIC, [["TCPROS"]])[2]
s = socket.create_connection((proto[1], int(proto[2])), timeout=10)
def enc(f):
    b=b""
    for k,v in f.items():
        kv=("%s=%s"%(k,v)).encode(); b+=struct.pack("<I",len(kv))+kv
    return struct.pack("<I",len(b))+b
def readn(n):
    b=b""
    while len(b)<n:
        c=s.recv(n-len(b))
        if not c: break
        b+=c
    return b
s.sendall(enc({"callerid":CALLER,"topic":TOPIC,"md5sum":"*","type":TYPE,"tcp_nodelay":"1"}))
readn(struct.unpack("<I",readn(4))[0])
s.settimeout(8)
try:
    mlen=struct.unpack("<I",readn(4))[0]
except Exception as e:
    sys.stderr.write("no message within timeout: %s\n"%e); sys.exit(2)
meta=readn(24)
s.close()
sizex,sizey=struct.unpack_from("<HH",meta,0)
xmin,xmax,ymin,ymax,res=struct.unpack_from("<5f",meta,4)
sys.stderr.write("sizex=%d sizey=%d xmin=%.3f xmax=%.3f ymin=%.3f ymax=%.3f res=%.5f\n"%(sizex,sizey,xmin,xmax,ymin,ymax,res))

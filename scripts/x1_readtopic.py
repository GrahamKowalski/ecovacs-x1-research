# Robot python2: subscribe to a topic, print type/md5/definition and first message hex, exit.
#   python2 x1_readtopic.py <topic>
import socket, struct, sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc
C="/valetudo_read"; topic=sys.argv[1]
def enc(f):
    b=b""
    for k,v in f.items():
        kv=("%s=%s"%(k,v)).encode(); b+=struct.pack("<I",len(kv))+kv
    return struct.pack("<I",len(b))+b
def rn(s,n):
    b=b""
    while len(b)<n:
        c=s.recv(n-len(b))
        if not c: raise EOFError()
        b+=c
    return b
m=xc.ServerProxy("http://127.0.0.1:11311")
ttype=dict(m.getTopicTypes(C)[2]).get(topic)
pubs=dict(m.getSystemState(C)[2][0]).get(topic)
if not pubs: print("NO PUBLISHER"); sys.exit()
uri=m.lookupNode(C,pubs[0])[2]
proto=xc.ServerProxy(uri).requestTopic(C,topic,[["TCPROS"]])[2]
s=socket.create_connection((proto[1],int(proto[2])),timeout=10)
s.sendall(enc({"callerid":C,"topic":topic,"md5sum":"*","type":ttype,"tcp_nodelay":"1"}))
hdr=rn(s,struct.unpack("<I",rn(s,4))[0])
f={}; o=0
while o+4<=len(hdr):
    n=struct.unpack("<I",hdr[o:o+4])[0]; o+=4; kv=hdr[o:o+n]; o+=n
    k,_,v=kv.partition(b"="); f[k.decode()]=v
print("type="+ttype+" md5="+f.get("md5sum",b"?").decode())
print("DEF<<<"+f.get("message_definition",b"").decode("latin1")+">>>")
data=rn(s,struct.unpack("<I",rn(s,4))[0]); s.close()
print("MSGHEX="+"".join("%02x"%b for b in bytearray(data)))

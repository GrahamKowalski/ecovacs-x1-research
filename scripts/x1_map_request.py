# Runs ON THE ROBOT (python2). Maps the byte layout of /task/WorkManage's request by
# probing: managetype=1 (a no-op stop while docked), everything else zero, and one
# candidate count byte set to 1 at a time. If the server then overruns, that byte is the
# low byte of a variable-array/string length prefix; the extra length it then demands is
# the element size. Counts never exceed 1, so no large allocation is triggered.
import socket, struct, sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc
SVC="/task/WorkManage"; CALLER="/valetudo_map"
def conn():
    code,msg,uri=xc.ServerProxy("http://127.0.0.1:11311").lookupService(CALLER,SVC)
    h,p=uri[len("rosrpc://"):].rsplit(":",1)
    return socket.create_connection((h,int(p)),timeout=10)
def hdr(fields):
    b=b""
    for k,v in fields.items():
        kv=("%s=%s"%(k,v)).encode(); b+=struct.pack("<I",len(kv))+kv
    return struct.pack("<I",len(b))+b
def rn(s,n):
    b=b""
    while len(b)<n:
        c=s.recv(n-len(b))
        if not c: raise EOFError()
        b+=c
    return b
def call(req):
    s=conn(); s.sendall(hdr({"callerid":CALLER,"service":SVC,"md5sum":"*","persistent":"0"}))
    rn(s,struct.unpack("<I",rn(s,4))[0])  # server header
    s.sendall(struct.pack("<I",len(req))+req)
    ok=bytearray(rn(s,1))[0]; resp=rn(s,struct.unpack("<I",rn(s,4))[0]); s.close()
    if ok==1: return "ok"
    if b"Overrun" in resp: return "overrun"
    if b"bad_alloc" in resp: return "badalloc"
    return "err:"+resp[:40].decode("latin1")
def mk(length, setpos=None):
    a=bytearray(length)
    if length>=1: a[0]=1           # managetype=1 (no-op)
    if setpos is not None and setpos<length: a[setpos]=1
    return bytes(a)
BASE=53
# sanity
assert call(mk(BASE))=="ok", "baseline 53 not ok"
assert call(mk(52))=="overrun", "52 not overrun"
fields=[]; off=2; calls=3
while off<BASE:
    r=call(mk(BASE,off)); calls+=1
    if r=="overrun":
        # count low byte: find element size by growing length
        elem=None
        for extra in (1,8,28,56,200):
            if call(mk(BASE+extra,off))=="ok": elem=extra; calls+=1; break
            calls+=1
        fields.append((off,"count",elem)); off+=4
    elif r=="ok":
        fields.append((off,"fixedbyte",None)); off+=1
    else:
        fields.append((off,r,None)); break
print("layout map (offset : kind : elem):")
for o,k,e in fields:
    print("  byte %2d : %s%s" % (o,k,"" if e is None else " elem=%d"%e))
print("service calls used:", calls)
# summarize count fields with element sizes
counts=[(o,e) for o,k,e in fields if k=="count"]
print("count/length fields:", counts)

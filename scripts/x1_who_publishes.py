# Runs on the robot: print publishers/subscribers of topics matching a pattern, and
# services matching it with their provider node.  python2 /tmp/x1_who_publishes.py <substr>
import sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc
pat = sys.argv[1].lower()
pubs, subs, srvs = xc.ServerProxy("http://127.0.0.1:11311").getSystemState("/valetudo_who")[2]
subs = dict(subs)
for t, nodes in sorted(pubs):
    if pat in t.lower():
        sys.stdout.write("%-45s pub=%s sub=%s\n" % (t, ",".join(nodes), ",".join(subs.get(t, []))))
for sname, nodes in sorted(srvs):
    if pat in sname.lower():
        sys.stdout.write("SRV %-41s by %s\n" % (sname, ",".join(nodes)))

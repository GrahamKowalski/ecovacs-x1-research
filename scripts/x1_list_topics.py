import sys
try:
    import xmlrpclib as xc
except ImportError:
    import xmlrpc.client as xc
m = xc.ServerProxy("http://127.0.0.1:11311")
CALLER = "/valetudo_lister"
types = dict(m.getTopicTypes(CALLER)[2])
pubs = dict(m.getSystemState(CALLER)[2][0])
rows = sorted(pubs.keys())
sys.stderr.write("=== %d published topics ===\n" % len(rows))
for t in rows:
    ty = types.get(t, "?")
    sys.stderr.write("%-40s %s\n" % (t, ty))

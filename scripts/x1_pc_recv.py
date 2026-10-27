import socket, sys, time, hashlib, os
host, port, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
expected = int(sys.argv[4]) if len(sys.argv) > 4 else 0
deadline = time.time() + 900
s = None
while time.time() < deadline:
    try:
        s = socket.create_connection((host, port), timeout=5); break
    except OSError:
        time.sleep(1)
if not s:
    print("no connection within 180s"); sys.exit(1)
h = hashlib.md5(); n = 0; last = 0
s.settimeout(120)
with open(out, "wb") as f:
    while True:
        try:
            b = s.recv(262144)
        except socket.timeout:
            print(f"recv timeout after {n} bytes"); break
        if not b:
            break
        f.write(b); h.update(b); n += len(b)
        if n - last >= 10*1024*1024:
            print(f"  {n} bytes..."); last = n
s.close()
status = "OK" if (expected and n == expected) else ("SHORT" if expected else "done")
with open(out + ".md5", "w") as m:
    m.write(f"{h.hexdigest()}  {os.path.basename(out)}\n{n} bytes ({status}, expected {expected})\n")
print(f"received {n} bytes ({status}, expected {expected}), md5 {h.hexdigest()} -> {out}")

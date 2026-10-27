import socket, sys, time
host, port, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
data = open(path, "rb").read()
deadline = time.time() + 600
s = None
while time.time() < deadline:
    try:
        s = socket.create_connection((host, port), timeout=5); break
    except OSError:
        time.sleep(1)
if not s:
    print("no connection"); sys.exit(1)
s.sendall(data)
s.shutdown(socket.SHUT_WR)
s.close()
print("sent %d bytes" % len(data))

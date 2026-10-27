"""Run a shell command on the robot through the unauthenticated telnetd shell
started over UART (telnetd -l /bin/sh -p 2323). PC side, Python 3, stdlib only.

    python x1_sh.py <host> "<command>" [timeout_s]
"""
import socket
import sys
import time

IAC, DONT, DO, WONT, WILL = 255, 254, 253, 252, 251


def strip_telnet(data, sock):
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b == IAC and i + 1 < len(data):
            cmd = data[i + 1]
            if cmd in (DO, DONT, WILL, WONT) and i + 2 < len(data):
                opt = data[i + 2]
                reply = WONT if cmd == DO else (DONT if cmd == WILL else None)
                if reply is not None:
                    sock.sendall(bytes([IAC, reply, opt]))
                i += 3
                continue
            i += 2
            continue
        out.append(b)
        i += 1
    return bytes(out)


def run(host, cmd, timeout=20, port=2323):
    s = socket.create_connection((host, port), timeout=5)
    s.settimeout(0.5)
    time.sleep(0.4)
    try:
        strip_telnet(s.recv(4096), s)
    except socket.timeout:
        pass
    marker = "__X1_DONE_%d__" % int(time.time())
    s.sendall((cmd + "\necho " + marker + "\n").encode())
    buf = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        buf += strip_telnet(chunk, s)
        # the marker appears once as the echoed command and once as the output
        if buf.count(marker.encode()) >= 2:
            break
    s.close()
    text = buf.decode("utf-8", "replace").replace("\r", "")
    lines = [l for l in text.split("\n") if marker not in l and l.strip() != cmd.strip()]
    return "\n".join(lines).strip()


if __name__ == "__main__":
    host, cmd = sys.argv[1], sys.argv[2]
    to = float(sys.argv[3]) if len(sys.argv) > 3 else 20
    print(run(host, cmd, to))

"""Drive the X1 uboot console over the UART (COM3). PC-side, pyserial.

  python x1_uboot.py catch            # spam the interrupt key, stop autoboot, land at prompt
  python x1_uboot.py cmd "<command>" [read_secs]   # send one uboot command, print output

uboot waits at its prompt once autoboot is stopped, so `catch` then separate `cmd` calls work.
Output is sanitised to printable ASCII.
"""
import re
import sys
import time

import serial

PORT = "COM3"
BAUD = 115200


def clean(b):
    return re.sub(r"[^\x20-\x7e\r\n]", ".", b.decode("latin1"))


def main():
    mode = sys.argv[1]
    ser = serial.Serial(PORT, BAUD, timeout=0.03)
    buf = b""

    if mode == "catch":
        deadline = time.time() + (float(sys.argv[2]) if len(sys.argv) > 2 else 30)
        last = 0.0
        while time.time() < deadline:
            now = time.time()
            if now - last > 0.02:
                ser.write(b" ")   # any key stops autoboot
                last = now
            c = ser.read(4096)
            if c:
                buf += c
            tail = buf[-120:]
            if b"Hit any key" in buf and (b"#" in tail or b"=>" in tail or b"$" in tail):
                time.sleep(0.25)
                ser.write(b"\r")
                time.sleep(0.4)
                buf += ser.read(16384)
                break
        time.sleep(0.3)
        buf += ser.read(16384)
        out = clean(buf)
        print(out[-2500:])
        print("\n=== prompt-reached:", "YES" if ("#" in out[-60:] or "=>" in out[-60:]) else "UNSURE")

    elif mode == "cmd":
        cmd = sys.argv[2]
        read_secs = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
        ser.reset_input_buffer()
        ser.write(cmd.encode() + b"\r")
        end = time.time() + read_secs
        while time.time() < end:
            c = ser.read(8192)
            if c:
                buf += c
        print(clean(buf)[-3500:])

    ser.close()


if __name__ == "__main__":
    main()

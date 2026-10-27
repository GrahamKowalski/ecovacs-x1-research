# Root + firmware dump, X1 Plus, 2026-10-25

Reproduced root on the owned X1 Plus (class `n4gstt`) and took a full firmware backup.
All items here are **observed** on the device unless noted. No secrets are included;
the serial, root password value, `did`, MQTT/product credentials and MACs are kept in
local-only storage (gitignored), never in the repo.

## 1. UART console

2×4 debug header behind the service flap, micro-USB socket below it. 3.3 V, `ttyS0`,
115200 8N1. Confirmed wiring (see [hardware.md](../docs/hardware.md) for the full pin map):

| Signal | Header pin | Adapter |
|---|---|---|
| GND | 6 | GND |
| SoC TX | 4 | RX |
| SoC RX | 3 | TX |

The micro-USB below the header did not enumerate on a PC. Pin 1 is a separate TX
(secondary MCU, `bank:N` hex dumps), not the Linux console.

## 2. Root password (confirmed on hardware)

Login `root` at `deboot login:`. The root password is derived per device from the serial
number using the public **eco_passwd** scheme, the same one documented by Dennis Giese
(DEF CON 32) and reimplemented in `samr28/ecovacs-t8-aivi-hacking` (`ecopasswd.py`). We use
those public tools and do not reproduce the algorithm, the salt, or any password here; see
[references/sources.md](../references/sources.md). Keeping the credential seed out of the repo
is the policy in [CONTRIBUTING.md](../CONTRIBUTING.md).

The one non-obvious input for this hardware was the machine/class token: the simplified form
on the public slides does not reproduce the password as-is. We resolved it from the device's
own firmware naming for the X1 Plus class (`n4gstt`); the specific value is kept in local
notes, not in this repo.

Entry over a raw serial console is error-prone (no echo at `Password:`, a long base64 string
with `+//=`). Driving the port programmatically, synchronising to the `login:` / `Password:`
prompts and sending exact bytes, was what finally confirmed it; manual paste of the correct
password was failing on newline and field errors, not on the value.

> The generator and the brute-force driver live in the fork's working tree as
> `eco_passwd_local.py` / `eco_passwd_bruteforce.py`, gitignored (`eco_passwd*`).

## 3. Firmware backup (pull over Wi-Fi, verified)

Robot on Wi-Fi (`wlan0`), PC on the same /24. Pull model (robot listens, PC connects out)
to avoid host firewall. Per image: `md5sum` on the device, `dd ... | nc -l -p 9000` on the
robot, PC connects and saves, then compare md5.

| Image | Source | Size (bytes) | Verified |
|---|---|---|---|
| rootfs | `/dev/ubi0_0` (static vol → squashfs data) | 79,024,128 | md5 match + `hsqs` magic |
| SYSINFO | `/dev/ubi2_0` | 2,285,568 | size exact |
| bootloader | `/dev/mtd0` | 5,242,880 | md5 match |
| uboot | `/dev/mtd1` | 3,670,016 | md5 match |

Images are stored **outside both repos** (copyright + embedded secrets). `/dev/ubi0_0` is a
static UBI volume, so it returns the real squashfs data size, not the 100 MiB volume capacity.

## Next

MITM the robot's MQTT/TLS to `mq-ww.ecouser.net` to capture real request/response pairs,
map payload first. See [local-interface.md](../docs/local-interface.md).

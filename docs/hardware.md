# X1 hardware knowns

All entries here are **third-party reported** unless marked otherwise; none have been
independently reproduced by this repo yet. Replace with **observed** entries (with your
own captures, redacted) as you verify them on the owned unit.

## Compute / storage

| Item | Value | Source |
|---|---|---|
| SoC | Horizon Robotics X3M (Sunrise/Journey family): 4× Cortex-A53 + Cortex-R5 + BPU, aarch64 | robotinfo.dev; itsjfx `x1_omni.md` (kernel string) |
| Platform codename | `px30-ai` / `AI_px30`, device `ZJ2102` | itsjfx `x1_omni.md` |
| OS | GNU/Linux, kernel 4.14.74 SMP PREEMPT, hostname `deboot`, ROS on top; U-Boot | itsjfx `x1_omni.md` |
| Flash | raw **SPI-NAND, 512 MB**; UBI/UBIFS + squashfs rootfs; A/B partitions | robotinfo.dev; itsjfx MTD table |
| RAM | 1 GB DDR4 | robotinfo.dev |
| Secondary DSP | Baidu DU1906 (wake word), own SPI flash | Giese DEF CON 32 / HITCON 2024 |
| Motor MCU | GD32F103VCT6 | robotinfo.dev |
| Wi-Fi | FN-Link 6223a (`wlan0`) | robotinfo.dev; code (`networkInterface: "wlan0"`) |

## UBI partitions (reported)

| Device | Contents |
|---|---|
| `/dev/ubiblock0_0` / `/dev/ubi0_0` | rootfs (squashfs, read-only) |
| `/dev/ubi1_0` | `/data` (ubifs) |
| `/dev/ubi2_0` | SYSINFO, **contains device secrets / MQTT info; never commit** |
| `/dev/ubi3_0` | AI models (squashfs) |

## UART

- `console=ttyS0,115200`, **3.3 V logic**, 8N1, no flow control.
- GND is the pad nearest the micro-USB port; TX/RX on the opposite side.
- Power sequence reported to matter: plug USB, connect adapter, then power on.
- **A 5 V adapter can damage the UART front-end. Use 3.3 V only.**
- No clean annotated pad photo is published, see [open questions](../research/open-questions.md).

### Observed on the owned X1 Plus (2026-10-25)

The debug header is **2×4 (8 pins)**, not the 2×8 reported for other Ecovacs Linux models.
It sits behind the service flap with a micro-USB socket directly below it. With a PC
attached to that micro-USB, nothing enumerated on USB, either while off or after power-on.

Pin numbering, with the micro-USB socket below the header:

```
 top row:     1  2  3  4
 bottom row:  5  6  7  8      (micro-USB below)
```

| Pin | Continuity to GND (off) | DC volts to GND (powered, idle) | Interpretation |
|---|---|---|---|
| 1 | no | 3.3 V steady | VCC, TX idle, RX or pull-up: undetermined |
| 2 | no | 10-15 mV, fluctuating | low/floating; not a UART idle level (hypothesis: USB D+/D−, SWD or unused) |
| 3 | no | 3.3 V | undetermined |
| 4 | no | 3.3 V | undetermined |
| 5 | no | 3.3 V constant | undetermined |
| 6 | **yes** |, | **GND** |
| 7 | no | ~1.7 mV | low; same hypotheses as pin 2 |
| 8 | no | 3.3 V | undetermined |

- Logic level is **3.3 V** (no 1.8 V or 5 V pins seen).

Listen-only test at 115200 8N1 (adapter GND on pin 6, adapter RX on the pin under test):

- **Pin 4 = SoC console TX.** Full boot log:
  - Horizon "HR-ROM" BL1, SPI NAND, LPDDR4.
  - U-Boot 2018.09 (built Nov 12 2021). "Hit any key to stop autoboot" with a 0 s delay.
  - Linux 4.14.74 SMP PREEMPT (built Mar 3 2022), `console=ttyS0,115200`, hostname
    `deboot`, busybox 1.24.1. This matches the third-party reports for the X1 Omni.
  - The log ends at a `deboot login:` prompt, followed by verbose startup-script tracing.
- **Pin 1 = a second TX** with different content: repeated `bank:N <hex> <hex>` lines.
  Hypothesis: debug output from a secondary MCU (e.g. the GD32 motor MCU), not the SoC.
  One capture on this pin was entirely unreadable.
- **Pin 3 = SoC console RX**, confirmed: with adapter TX on pin 3, the `deboot login:`
  prompt accepts input and a root login succeeded.
- Pins 5 and 8 stay at 3.3 V and were never driven; pin 8 (below pin 4) is the likely VCC.
  Leave both unconnected.

**Confirmed wiring for the SoC console (`ttyS0`, 115200 8N1, 3.3 V):**

| Signal | Header pin | To USB-UART adapter |
|---|---|---|
| GND | 6 | GND |
| SoC TX | 4 | RX |
| SoC RX | 3 | TX |

This is the first published annotated pinout for the X1 (Plus); resolves open question 5.

**The boot log prints secrets in clear text** (startup-script tracing shows a password and
the setup-AP SSID). Raw logs stay out of every repo. Quote only redacted excerpts.

### On-device facts (observed, root shell, X1 Plus)

- **Compute:** board reports `Model: Hobot XJ3 Soc Board`, `base board type: X3 DVB`
  (Horizon X3). Kernel `Linux 4.14.74 #2 SMP PREEMPT aarch64`, hostname `deboot`,
  busybox 1.24.1. U-Boot 2018.09 (built Nov 12 2021), autoboot delay 0 (can't key-interrupt).
- **Versions:** `hw_arm 0.0.3`, `fw_arm 1.7.2`. Device class/`type` `n4gstt` (X1 Plus).
- **Root:** `id` → `uid=0(root)`. Rootfs is read-only squashfs, so persistence needs a reflash.
- **UBI volumes** (from `ubinfo -a`; LEB 253952 B):
  | Device | Volume | Size | Mount | Notes |
  |---|---|---|---|---|
  | `ubi0_0` | rootfs | 100 MiB vol / 79 MiB data (static) | `/` squashfs ro | the firmware image |
  | `ubi1_0` | userdata | 162 MiB | `/data` ubifs rw | runtime data |
  | `ubi2_0` | sys | 2.1 MiB |, | **SYSINFO: device secrets** |
  | `ubi3_0` | model | 130 MiB | `/model` squashfs ro | AI/camera models |
- **Raw MTD backups taken:** `mtd0` bootloader (5 MiB), `mtd1` uboot (3.5 MiB).
- **Cloud endpoint:** SYSINFO `lb` = `mq-ww.ecouser.net` (MQTT). This is the MITM redirect target.
- **Firmware image naming:** `zj2102-x3-n10_fw-<ver>.bin` (per robotinfo for class `n4gstt`).

## Variants

X1 **Plus / Omni / Turbo** differ only in mop system and dock (Plus = auto-empty;
Turbo = cold-air wash/dry; Omni = hot-air). Core compute/flash/root path is reported
identical. Only the Omni has a published writeup, Plus/Turbo sameness is **hypothesis**
until confirmed on hardware.

## Caution

- Do **not** accept an OTA update on a unit you intend to root; newer firmware can close
  the path. X1 Omni is EOL/end-of-sale.

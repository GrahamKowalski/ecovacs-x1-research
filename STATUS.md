# Research status, 2026-10-25

> Full session wrap-up and resume guide: [research/handoff-2026-10-25.md](research/handoff-2026-10-25.md).

**Goal:** 100% local control of the Ecovacs Deebot X1 with a Home Assistant integration
comparable to Valetudo, by completing the ValetudoEV X1 implementation.

**Where it stands:** Layer 1 (root) is now **reproduced on the owned X1 Plus**, UART
console, serial-derived root password, and a verified full firmware backup. The
ValetudoEV X1 app layer is still an early stub (battery + mock map); no usable local
cleaning control exists off-the-shelf yet. Next is MITM capture of the robot's MQTT
traffic to build the real map parser.

## Layer 1, root / unlock (reproduced 2026-10-25)

See [research/root-and-firmware-dump-2026-10-25.md](research/root-and-firmware-dump-2026-10-25.md).

| Item | Evidence level | Status |
|---|---|---|
| UART console `ttyS0,115200`, 3.3 V, **2×4 header, GND=pin6, TX=pin4, RX=pin3** | **observed (X1 Plus)** | Reproduced; annotated pinout in [hardware.md](docs/hardware.md) |
| Root password from serial, `MACHINE=zj2102-x3-n10`, last-8 SN, `sha256sum` base64 form | **observed (X1 Plus)** | Confirmed via automated UART login |
| Firmware dump via `dd` \| `nc` (rootfs, SYSINFO, bootloader, uboot) | **observed (X1 Plus)** | Done; md5-verified, stored outside repos |
| Persistent SSH via `patch-rootfs` + reflash (read-only squashfs) | third-party reported | Not yet attempted; brick risk on reflash |

## Layer 2, ValetudoEV X1 implementation (the work)

| Item | Evidence level | Status |
|---|---|---|
| Only `EcovacsWifiConfigurationCapability` registered for X1 | observed (code audit) | Confirmed in `EcovacsX1OmniValetudoRobot.js` |
| `pollState()` parses only battery level | observed (code audit) | Confirmed; charge/station/stats requested but unparsed |
| Real map **working end to end** | **observed (X1 Plus)** | Live-fetched via `/map/GetCurrentCompressMap` (TCPROS, reflash-free), decoded by `EcovacsMapParser` (tiled LZMA1, 800×800), rendered. See [map note](research/map-format-decoded-2026-10-25.md) |
| Robot + charger placement on map | **observed (X1 Plus)** | world-to-grid transform in `EcovacsMapParser.POSE_TO_ENTITY`; robot position validated on-device |
| Battery + charge state | **observed (X1 Plus)** | `EcovacsRobotStateParser` decodes `/robot/Robot`; validated (battery 40%, on charger) |
| ValetudoEV last code push ~2025-05-26 | observed (GitHub API) | Development appears stalled |
| Local control interface (`Ecocloud` P2P / `mdsctl`) | hypothesis / partial | Message shapes need live capture |
| ~30+ Valetudo capabilities unimplemented for X1 | observed (code audit) | See [capability matrix](docs/capability-matrix.md) |

## Next steps

1. **Coordinate before coding**, check with itsjfx / the Valetudo rooting community
   whether there is unpushed X1 work and why it stalled. Avoid duplicating effort.
2. Reproduce root on the owned X1 and capture the robot's live local/cloud MQTT traffic.
3. Build the real **map parser** first (biggest user-visible gap), then `BasicControl`.
4. Record each capability's request/response evidence in the capability matrix.

See [licensing-and-governance.md](docs/licensing-and-governance.md) for the
contribute-vs-fork decision this hinges on.

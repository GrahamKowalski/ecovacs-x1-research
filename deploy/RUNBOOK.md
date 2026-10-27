# X1 deployment runbook (reflash-free install of the local-control backend)

Goal: run the fork's backend on the robot so it starts on boot and controls the vacuum
locally over ROS, with no cloud. Based on the device analysis in the research notes.

## Target architecture (verified)

- Rootfs `/` is a **static UBI squashfs volume** `rootfs` on `ubi0` (NAND `mtd5` "system"),
  v4.0, **gzip, 128 KiB blocks**, 75 MiB of data in a 100 MiB (413 LEB) volume.
- `/data` (`ubi1`, ubifs) is writable + persistent, ~120 MiB free. `/etc` is read-only.
- There is **no equal-size A/B slot for the rootfs** (`system_b` mtd6 is only 31 MiB), so the
  update is an **in-place volume replace** via `ubiupdatevol`, recoverable only via UART +
  the backup, not a seamless slot switch.
- On-device tools present: `ubiupdatevol`, `ubiformat`, `ubinize`, `nandwrite`, `flash_erase`.
- Boot runs `/etc/rc.local` at the end of `rc.sysinit` (currently empty) - our startup hook.
- Secure/verified boot covers the bootloader -> uboot -> kernel chain only; the rootfs is
  mounted unverified, so a modified squashfs boots (keep bootloader/uboot/kernel stock).

## PREREQUISITE (DONE, committed bf4280b0): ROS link is the primary data path

Today `EcovacsX1OmniValetudoRobot.pollState()` goes through the Ecocloud mock, and the
constructor sets Ecocloud up unconditionally (throws without TLS certs). For a functional
local deploy the backend must read state/map from the ROS link it already has, and treat
Ecocloud as optional. Do this before building a final image:
1. In `pollState()` / `buildMap()`, when `rosLink` is active, serve battery/charge/status and
   map from the ROS link (handleRobotState/handleWorkState/handleMapData already parse them);
   drive them from the subscriptions rather than an Ecocloud poll.
2. Make the Ecocloud setup optional (skip or tolerate missing certs) when `ecovacsRosMasterUri`
   is set, OR keep certs in the image (this runbook bakes them in, so it will not throw).
Done: pollState serves from the ROS subscriptions when ecovacsRosMasterUri is set, and the
Ecocloud TLS requirement is non-fatal in that mode (and the image bakes certs anyway).

## Artifacts (in this `deploy/` dir)

- `rc.local` - boot hook: persistent telnet, seed config, start the backend.
- `valetudo_config.seed.json` - config template. Fill `deviceId`/`mId`/`resourceId` from the
  device's stock config (on the robot) before first boot; set `ecovacsRosMasterUri` to
  `http://127.0.0.1:11311`.
- `build_rootfs.sh` - builds the modified squashfs in a Linux container.
- Backend binary: `ecovacs-local/build/aarch64/valetudo` (rebuilt with the control capabilities
  and the OpenAPI schema; 37.6 MB).

## Build the image (needs a Linux env: Docker Desktop running, or WSL/native Linux)

Docker daemon was NOT running during prep; start Docker Desktop first. From Git Bash use
`MSYS_NO_PATHCONV=1`:

```sh
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "E:/Documents/Programming/ecovacs-x1-research:/work" \
  -v "C:/Users/Graham/Desktop/x1/dump:/dump:ro" \
  -v "E:/Documents/Programming/ecovacs-local/build/aarch64:/bin-in:ro" \
  -v "E:/Documents/Programming/ecovacs-local/local/ecocloud-tls:/certs:ro" \
  debian:12 sh -c "apt-get update && apt-get install -y squashfs-tools && sh /work/deploy/build_rootfs.sh"
```

Output: `deploy/new_rootfs.squashfs`. Confirm it is <= 100 MiB (the volume size). Mount-check
it (`unsquashfs -l`) to verify `/usr/local/bin/valetudo`, `/etc/rc.local`, and the certs are present.

## Flash (on the robot; keep a UART tether ready)

1. Ensure a UART console is attached and the full backup (`rootfs_ubi0_0.img`) is at hand.
2. Push the image to the writable partition: `nc` it to `/data/new_rootfs.squashfs`
   (`x1_pc_send.py`), md5-verify both sides.
3. Replace the rootfs volume in place:
   ```sh
   ubiupdatevol /dev/ubi0_0 /data/new_rootfs.squashfs
   sync; reboot
   ```
4. On reboot the backend starts from `rc.local`; reach the Valetudo UI on port 80 and the
   recovery shell on telnet 2323.

## Recovery (if it does not boot)

Over UART, re-attach ubi if needed and restore the stock volume:
```sh
ubiupdatevol /dev/ubi0_0 /path/to/rootfs_ubi0_0.img   # the backup
sync; reboot
```
If UBI itself is wedged, `ubiformat`/`nandwrite` the `system` mtd from the backup. The kernel,
uboot and bootloader are untouched, so the device always reaches at least the bootloader/UART.

## Backend runtime (Node 18 + madvise patch) - REQUIRED for this kernel

The robot runs kernel 4.14.74 (aarch64, glibc 2.23, 4 KiB pages, no THP). This
constrains the backend build:
- Node 20/22's V8 crashes at startup ("Check failed: 0 == ret") because the
  kernel lacks MAP_FIXED_NOREPLACE (needs >= 4.17). **Build with Node 18.**
- Node 18 cannot `require()` ESM, so the three ESM-only deps are pinned to their
  last CommonJS majors in the fork (crc 3.8.0, express-rate-limit 6.11.2,
  jstoxml 2.2.2). Committed to the fork.
- `lzma/src/lzma_worker.js` is added to pkg `assets` (loaded via a computed path
  pkg cannot trace). Committed to the fork.
- Even on Node 18, V8 crashes later when it returns memory to the OS:
  `madvise(MADV_DONTNEED)` fails on this kernel and V8 CHECK-crashes in
  `MemoryChunk::DiscardUnusedMemory`. Fix: `deploy/patch_madvise.py` rewrites the
  single libc madvise stub's `bl __syscall_ret` to `mov x0,#0`, so the syscall
  still runs (memory is freed when the kernel allows) but the return is forced to
  0 and V8 never sees a failure. Build flags also include `no-memory-reducer`.

Build the binary (from `ecovacs-local/backend`):
```sh
PKG_CACHE_PATH=../build_dependencies/pkg ../node_modules/.bin/pkg \
  --targets node18-linuxstatic-arm64 --compress Brotli --no-bytecode \
  --public-packages "*" --options "expose-gc,max-heap-size=64,no-memory-reducer" \
  . --output ../build/aarch64/valetudo
python ../../ecovacs-x1-research/deploy/patch_madvise.py ../build/aarch64/valetudo
```
`build_rootfs.sh` re-applies the patch (idempotent) when baking the image.

## OTA iteration (no reflash)

The flashed rootfs runs `/data/valetudo` in preference to the baked binary. To
update the backend without reflashing: push the new binary over the persistent
telnet (`nc -l -p PORT > /data/valetudo.new` on the robot, `x1_pc_send.py` from
the PC), md5-verify, `chmod +x /data/valetudo.new`, `mv` it to `/data/valetudo`,
and reboot (rc.local restarts it). The config seed must be a full valid config
(see valetudo_config.seed.json); a minimal one fails schema validation and gets
rewritten with defaults, which drops the ROS `implementationSpecificConfig`.

**Set the execute bit, or the update silently no-ops.** `nc` writes the received
file as `rw-r--r--` (no execute bit) and `mv` preserves that mode, so a binary
pushed this way is NOT executable. The boot hook only runs `/data/valetudo` when
it is executable (`[ -x /data/valetudo ] && BIN=/data/valetudo`); a non-executable
one is skipped and rc.local falls through to the baked `/usr/local/bin/valetudo`,
so your new build never runs and MQTT/Home Assistant shows the old behaviour (or
`unavailable` across the reboot). Always `chmod +x` the file before or after the
`mv`, and confirm with `[ -x /data/valetudo ]` before rebooting. Observed on
2026-10-27 after an OTA: the transfer and md5 were correct but the binary was
mode 644, so the reboot ran the baked copy instead.

Rollback has no second on-device copy to depend on (`/data` is ~149 MiB and two
full binaries plus a backup will not fit; `cp` fails with "No space left on
device"). The real fallback is the baked `/usr/local/bin/valetudo`: if a pushed
binary misbehaves, `rm -f /data/valetudo` then `reboot` boots the known-good
flashed copy. Keep the `mv` (a same-filesystem rename, needs no free space)
rather than `cp` when swapping the staged file in.

## Status

DEPLOYED AND RUNNING (2026-10-26). Rootfs flashed; `/data/valetudo` is the
patched Node 18 build; backend auto-starts on boot, serves the web UI/API on
port 80 over the LAN, and reads live state/map from the ROS link (battery,
attachments, status decoded; 9 capabilities registered). Stable across idle and
API load; survives reboot. Remaining user step: configure MQTT in the Valetudo
UI to surface the vacuum in Home Assistant.

History (pre-deploy): READY TO FLASH (pending on-device execution with UART tether).
- Backend binary rebuilt with the control capabilities, OpenAPI schema, and the ROS-primary
  integration: `ecovacs-local/build/aarch64/valetudo` (37.6 MB).
- Image built and validated: `deploy/new_rootfs.squashfs`, 91.4 MiB (8.6 MiB headroom under the
  100 MiB volume), squashfs v4.0 / gzip / 128 KiB, contains the backend, our rc.local, the certs
  and config seed; stock content intact.
- Pure-local build: no Ecocloud certs baked, so the cloud mock is disabled and the backend
  runs ROS-only. No Ecovacs device ids needed (they only matter for the inert cloud mock).
- Image contents verified: updated binary (37.6 MB), our rc.local, clean config seed, stock
  rootfs intact.
- Remaining is ONLY the on-device flash: push `new_rootfs.squashfs` to /data, md5-check,
  `ubiupdatevol /dev/ubi0_0 /data/new_rootfs.squashfs`, reboot. UART tether + backup ready.
## Home Assistant (verified: Mosquitto broker add-on + MQTT integration both running)

After flash, in Valetudo's UI (http://<robot-ip>) > Settings > Connectivity > MQTT:
- Broker host = the HA host's LAN IP, port 1883 (the running `core_mosquitto` add-on).
- Credentials = an MQTT user (an HA user, or a Mosquitto add-on local user).
- Enable Home Assistant autodiscovery. The `vacuum` entity (battery, state, and the controls:
  start/stop/home/goto/segment-clean/fan/water/carpet/locate) then auto-appears in HA.
- Live map in HA: install the Valetudo map card (HACS) pointed at the MQTT map topic.

## OTA updates after the first flash (YES)

The first flash bakes a persistent telnet (rc.local) and the backend into the rootfs, so network
root access survives every reboot - no more UART dependency. After that:
- Backend updates are brick-free and need no reflash: copy a new aarch64 `valetudo` to
  `/data/valetudo` (over the network) and restart. rc.local prefers `/data/valetudo` over the
  baked copy, so the rootfs is never touched for a backend update.
- Non-backend rootfs changes: push a new squashfs and `ubiupdatevol /dev/ubi0_0` (network), then
  reboot. A bad rootfs flash that will not boot still needs UART to recover, so prefer the
  /data backend path for routine updates.
- Kernel/uboot/bootloader are left stock and not updated by us (they are signature-checked).

Nothing has been flashed.

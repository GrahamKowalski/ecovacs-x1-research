# X1 deployment persistence: what boot hooks actually exist (2026-10-26)

Correcting an earlier optimistic note. Investigated how to run our software (and a persistent
telnet/ssh) across reboots, from the writable partition, without a firmware flash.

## Filesystem / boot facts

- `/` is read-only squashfs (`/dev/ubiblock0_0`, `ubi.mtd=5`), 100% full. `/etc` cannot be edited.
- `/data` (`/dev/ubi1_0`, ubifs) is read-write + persistent, ~120 MB free. `HOME=/data`.
- `/var/*` are symlinks into `/tmp/root/var` = tmpfs (volatile). `/tmp`, `/run` volatile.
- A/B slots: `system`(mtd5)/`system_b`(mtd6), `boot`/`boot_b`. Official OTA tools present
  (`otaupdate`, `hrut_otaserver`) but take Ecovacs-signed Horizon packages (not usable by us).
- Boot: inittab -> `/etc/rc.sysinit` -> sources `/etc/rc.conf` `DAEMONS=...` -> runs each
  `/etc/rc.d/<name>.sh start` (`!name` = skipped, `@name` = backgrounded) -> `sh /etc/rc.local`.

## Why there is NO clean, safe /data boot hook

- `autostart.sh` (which globs and runs `/data/autostart/*.sh`) is in DAEMONS as **`!autostart.sh`
  = skipped**. `/etc` is read-only, so it cannot be re-enabled.
- `/data/autostart/medusa.sh` and `/data/autostart/deebot.sh` are **disable switches**: the
  enabled `medusa.sh`/`deebot.sh` do `if [ -f /data/autostart/<name>.sh ]; then exit; fi`.
  Creating them STOPS the core robot stack (`/node`). Do not create these.
- `crond.sh` **overwrites** `/var/spool/cron/crontabs/root` with a single autoOTA line every
  boot, and `/var/spool` is tmpfs. Any cron entry we add is erased on reboot.
- `/etc/rc.local` is 0 bytes. A sweep of every enabled boot script found none that execs an
  arbitrary `/data` script. `/data/awss_hook.sh` is run only on wifi/key events, not boot.
- `deebot.sh` sets `LD_LIBRARY_PATH=/data/opt_lib` but `rm -fr`s that dir every boot.

## Consequence

A small, safe, no-flash autostart (e.g. a persistent telnetd/dropbear) is **not available**.
Persistent on-boot execution requires modifying the read-only `system` image and flashing it
to the inactive A/B slot (`system_b`), then switching slots. That is the real deployment, not a
"small" step. It is recoverable (A/B fallback + full backups + UART), but carries boot risk and
depends on whether the bootloader signature-verifies the system image (to be analyzed from the
uboot/bootloader dump before attempting).

## Recommendation

- For the research phase, keep the volatile `telnetd -l /bin/sh -p 2323`; if the robot reboots,
  restart it over UART. The robot's uptime is long (days), so this is low friction.
- Persistent access comes bundled with the real deployment anyway (the backend has to run on
  boot, which needs the system-image flash). Build the backend capabilities offline first; do
  the signed-boot analysis; then do one system-image A/B flash that includes both the backend
  and a persistent shell.
- dropbear/sshd are NOT in the image (only busybox telnetd + nc); a system-image build is the
  point to add dropbear for key-based SSH instead of plaintext telnet.

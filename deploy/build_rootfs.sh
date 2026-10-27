#!/bin/sh
# Build a modified X1 rootfs squashfs (stock + Valetudo backend + startup hook), matching
# the device's squashfs params (v4.0, gzip, 128 KiB blocks). Run in a Linux container with
# squashfs-tools, as root (to preserve perms/symlinks/device nodes). Produces new_rootfs.squashfs.
#
#   docker run --rm -v "<repo>:/work" -v "<dump>:/dump:ro" -v "<fork build>:/bin-in:ro" \
#       debian:12 sh -c "apt-get update && apt-get install -y squashfs-tools python3 && /work/deploy/build_rootfs.sh"
#
# The backend binary MUST be the Node 18 aarch64 build (newer Node V8 crashes on this
# kernel 4.14). Build it from backend/ with:
#   PKG_CACHE_PATH=../build_dependencies/pkg pkg --targets node18-linuxstatic-arm64 \
#     --compress Brotli --no-bytecode --public-packages "*" \
#     --options "expose-gc,max-heap-size=64,no-memory-reducer" . --output ../build/aarch64/valetudo
# This script also applies patch_madvise.py (idempotent) so the madvise(MADV_DONTNEED)
# failures on 4.14 do not crash V8. See that script and RUNBOOK.md for why.
set -e
SRC=/dump/rootfs_ubi0_0.img          # stock rootfs squashfs (read-only)
OUT=/work/deploy/new_rootfs.squashfs
VALETUDO=/bin-in/valetudo            # fork build/aarch64/valetudo (Node 18 build)
CERTS=/certs                         # the fork's local/ecocloud-tls, mounted at /certs
RF=/tmp/rootfs

rm -rf "$RF"; unsquashfs -d "$RF" "$SRC"

# Apply the madvise patch to a private copy (keep the mounted /bin-in read-only).
cp "$VALETUDO" /tmp/valetudo.patched
python3 /work/deploy/patch_madvise.py /tmp/valetudo.patched
install -D -m 0755 /tmp/valetudo.patched "$RF/usr/local/bin/valetudo"
install -D -m 0644 /work/deploy/valetudo_config.seed.json "$RF/usr/local/share/valetudo/valetudo_config.seed.json"
install -m 0755 /work/deploy/rc.local "$RF/etc/rc.local"
# Pure-local (ROS) build: no Ecocloud TLS certs, so the robot runs ROS-only and the cloud
# mock is disabled (EcovacsX1OmniValetudoRobot treats missing certs as non-fatal in ROS mode).
# To ship the cloud mock too, re-add: install -D "$CERTS/server.key" .../ecocloud.key etc.

rm -f "$OUT"
mksquashfs "$RF" "$OUT" -noappend -comp gzip -b 131072 -all-root
echo "built $OUT"; ls -l "$OUT"
echo "rootfs UBI volume is 100 MiB (413 LEBs); image must be <= that."

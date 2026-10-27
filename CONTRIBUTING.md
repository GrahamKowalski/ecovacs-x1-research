# Contributing

## Evidence labels

Label every observation as one of:

- **observed**, you saw it yourself on a device or in a capture you took. Include the
  firmware version, how you captured it, and a redacted excerpt.
- **third-party reported**, from someone else's writeup, repo, or talk. Link the source.
- **hypothesis**, your inference. Say what would confirm or refute it.

Prefer **live capture of the robot's own traffic** (e.g. MITM of its MQTT/TLS session,
on-device logs) as primary evidence over reading someone else's client source. When
you implement a capability, the authoritative evidence is a captured request/response
pair from the real device, not a guess at the message shape.

## Redaction, do not commit secrets

The X1's root password is **derived from its serial number**, so the serial is a
credential. Never commit any of:

- Device **serial number** (20-char, under the dust bin) or the derived root password
- `deviceId`, `mId`, `resourceId`, MAC, or MQTT username/password (from SYSINFO / `ubi2_0`)
- Ecovacs account tokens, cloud credentials, or auth keys
- Firmware images, rootfs/UBI dumps, or any extracted binary (copyright + embedded secrets)
- MITM CA **private** keys

Redact captures before adding them. When in doubt, keep it out. See [.gitignore](.gitignore)
for the patterns that keep raw dumps and captures out of the tree.

## Pull requests

Documentation corrections, capability-matrix updates backed by captures, and
non-destructive analysis tools are welcome. Code intended for ValetudoEV itself should
go upstream to that project (see
[docs/licensing-and-governance.md](docs/licensing-and-governance.md)); this repo holds
the research that informs it.

No unsupported claims of working features, and no proprietary firmware.

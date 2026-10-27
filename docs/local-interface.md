# The X1 local control interface (the RE target)

To implement capabilities we must know the robot's own request/response protocol. The
method, consistent with how this research is done elsewhere, is **capture the live
device traffic and report what it does**, not infer the protocol from someone else's
client source.

## What's known about the channel

- Stock, the robot talks to the Ecovacs cloud over **MQTT (TLS)** plus a REST/XMPP
  history. ValetudoEV stands in as that endpoint: `Ecocloud.js` binds `127.0.0.1:443`
  when running on the robot (embedded) or `0.0.0.0:1883` otherwise. **third-party / code audit**
- Commands observed in the stub's `pollState()`: a `P2P` message, command `getInfo`,
  with args `["getStationState", "getBattery", "getChargeState", "getStats"]`.
  The battery branch reads `body.data.getBattery.data.value` and
  `body.data.getChargeState.data.isCharging`. **observed (code audit)**, shows the
  envelope shape but only a few fields.
- On-device helpers reported by itsjfx for pulling identifiers/secrets:
  `mdsctl bumbee '{"todo":"QueryIotInfo"}'` (MQTT info),
  `mdsctl sys0 '{"pid_get":"get_all"}'` (plus MAC). **third-party reported.**

## How to capture (planned method)

1. Root the X1 and get persistent SSH (Layer 1).
2. Put a MITM proxy between the robot and the network so its MQTT/TLS session is
   readable (itsjfx ships `bin/capture-mitm`, `bin/sslkeylogfile`, and a `--add-cert`
   path in `patch-rootfs` to trust the MITM CA). Keep the **CA private key out of git.**
3. Drive each function from the **stock Ecovacs app** against the robot and record the
   resulting request/response. That captured pair is the spec for the corresponding
   Valetudo capability.
4. Redact identifiers (serial, deviceId, mId, resourceId, MAC, tokens) before saving
   any excerpt here.

## What to document per capability

For each capability in the [matrix](capability-matrix.md), record in a dated
`research/` note:

- The triggering app action (e.g. "start cleaning", "clean living room", "mop dry").
- The request: message type, command, args/payload (redacted).
- The response and any async state/push that follows.
- The mapping into Valetudo's model (which state attribute / capability call / map field).

The map payload deserves its own note: its grid/coordinate encoding is the hardest and
most valuable thing to pin down, since the current `buildMap()` is pure mock data.

## Command surface (observed, rootfs code audit, 2026-10-25)

From the owned X1 Plus firmware (`/etc/conf/func_table.conf`, `/etc/conf/medusa/deebot_x3.conf`
in the rootfs dump). This is the device's own command vocabulary, authoritative for *names*
and request/response pairing, but **not** the payload wire format (that still needs a live
capture or binary RE). Convention: `getX` request → `onX` async response/push; `setX` to change.

| Group (`func_table`) | Commands | Maps to |
|---|---|---|
| `map_info` | `getMapInfo`/`onMapInfo`, `getPos`/`getPos_V2`/`onPos`, `getMapState`/`onMapState`, `getMajorMap`/`onMajorMap`, `getMinorMap`/`onMinorMap`, `getMapTrace`/`onMapTrace`, `getMapSet`/`getMapSubSet`/`setMapSet`/`setMapSubSet`/`onMapSet`, `clearMap`, `readSmartVW` | **map parser**, segments, virtual walls/no-go |
| `clean_logic` | `clean`, `charge`, `move`, `getBlock`/`setBlock`, `getSched`/`setSched`, `getBreakPoint`, `getAdvancedMode` | BasicControl, ManualControl, no-go, schedule |
| `water_box` | `getWaterInfo`/`setWaterInfo`/`onWaterInfo` | WaterUsageControl |
| (info) | `getInfo`/`onInfo`, `getBattery`/`onBattery`, `getSpeed`/`setSpeed`/`onSpeed`, `getLifeSpan`/`resetLifeSpan`, `getDusterRemind`, `getCarpertPressure`, `getLight`, `getSleep`, `getNetInfo` | FanSpeed, consumables, carpet |
| `clean_status` | `getStats`/`getTotalStats`/`getCleanRecord`/`emptyCleanRecord`/`onStats` | CurrentStatistics, TotalStatistics |
| (status) | `getCleanInfo`/`onCleanInfo`, `getChargeState`/`onChargeState`, `getRelocationState`/`onRelocationState`, `getError`/`onError`, `onEvt` | state/dock/error attrs |
| `multi_map` | `getMultiMapState`/`setMultiMapState`, `getCachedMapInfo`/`onCachedMapInfo`/`setCachedMapInfo` | PersistentMap / multi-map |
| (AI) | `getRecognization`/`setRecognization`, `getMapPoint`/`setMapPoint`, `getAIMap`/`readAIMap`/`onAIMapAndMapSet` | AI obstacle avoidance |
| `offlinemap` | `offPos`, `offMajorMap`, `offMinorMap`; report\* variants (`reportMajorMap`, …) | map push path |

### Internal architecture (observed)

- **`medusa`** is the internal message bus/router; plugins live in `/usr/lib/medusa/`. Its
  `mqtt` plugin bridges to the cloud (`lb.ecouser.net` → `mq.ecouser.net`). Routes are
  explicit pairs in `deebot_x3.conf` (e.g. `["mqtt","bumbee"]`, `["camera0","bpu"]`).
- **`mdsctl`** is the medusa control CLI (`mdsctl <module> '<json>'`); used to query
  `bumbee`/`sys0` for IoT info. Candidate reflash-free tap for `onMajorMap` plaintext.
- The map is produced by ROS nodes `liberos_node_slam.so`, `liberos_node_house_layout.so`,
  `libslam.so` and published through medusa as `onMajorMap`/`onMinorMap`/`onPos`.

### Reflash-free capture levers (observed)

- `/etc/hosts` → symlink to `/tmp/root/etc/hosts` (writable): can redirect `mq.ecouser.net`.
- `deebot.sh` sets `LD_LIBRARY_PATH=/data/opt_lib` (`/data` writable): possible lib injection.
- `/etc/ssl/certs` is a real dir on the **read-only** rootfs: adding a MITM CA needs a reflash.
- Net effect: *active* redirect/MITM still needs a reflash (CA trust); a *local medusa tap*
  (via `mdsctl`/a medusa socket) may yield `onMajorMap` plaintext with root only.

## Methodology note

Evidence is the **live captured exchange from the real device**. Reading other clients'
source (deebot-client, sucks, bumper) is fine for orientation and cross-checking, but a
capability is only marked `done` when backed by a captured request/response from the
device itself.

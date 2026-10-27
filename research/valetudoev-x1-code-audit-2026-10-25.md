# ValetudoEV X1 code audit, 2026-10-25

**observed (code audit)** of `itsjfx/ValetudoEV` at `master` via the GitHub API/raw
files. No device involved. Purpose: establish exactly what the X1 implementation does
and does not do, as the baseline for the capability matrix.

## Repo signals

- Default branch `master`, the only branch; `pushed_at` **2025-05-26** per the GitHub
  API. Suggests development stalled ~17 months before this audit.
- Description: "Cloud replacement for vacuum robots enabling local-only operation."
- License: Apache-2.0.

## The one Ecovacs robot

`backend/lib/robots/ecovacs/EcovacsX1OmniValetudoRobot.js`:

- `getManufacturer()` → `"Ecovacs"`, `getModelName()` → `"X1 Omni"`.
- Constructor sets up `Ecocloud` bound to `127.0.0.1:443` (embedded) or `0.0.0.0:1883`,
  then **registers exactly**:
  - `EcovacsWifiConfigurationCapability` (`wlan0`)
  - `LinuxWifiScanCapability` (`wlan0`), only when `config.embedded === true`
- A long block of `this.registerCapability(new capabilities.Mock*…)` lines for
  BasicControl, FanSpeed, WaterUsage, ZoneCleaning, MapSegmentation, GoToLocation,
  AutoEmptyDock*, MopDock*, Consumable, Statistics, Speaker, DnD, KeyLock, ManualControl,
  Obstacle/Pet/Collision avoidance, Carpet*, VoicePack, etc., **all commented out.**
- `pollState()` sends `Ecocloud.MESSAGE_TYPES.P2P`, `"getInfo"`,
  `["getStationState", "getBattery", "getChargeState", "getStats"]`.
- `parseAndUpdateState()` parses **only battery**: level from
  `getBattery.data.value`; charging flag from `getChargeState.data.isCharging`.
  `getStationState` and `getStats` are requested but not parsed.
- `onIncomingCloudMessage(msg)` → `return true;` (stub; commented `console.log`).
- `buildMap()` builds a **mock** `ValetudoMap`: a square floor, a square wall, a fixed
  charger point and a fixed robot point at a hardcoded angle. No real map decoding.
- Several `// TODO`: `extends EcovacsValetudoRobot`, `use mdsctl mid`, `get deviceId/mId/
  resourceId` read from `implementationSpecificConfig` (stubbed).

## Ecovacs-specific capabilities present

`backend/lib/robots/ecovacs/capabilities/` contains only:
- `EcovacsWifiConfigurationCapability.js`
- `index.js`

i.e. **one** real Ecovacs capability. The generic core capabilities and their MQTT
handles all exist, but nothing connects them to the X1.

## Conclusion

Off-the-shelf, a rooted X1 running this would surface in Home Assistant with **battery
percentage and a fake map** and essentially nothing actionable. Every cleaning/mapping/
dock function is unimplemented. The work is to implement those capabilities against the
robot's local interface, see [capability-matrix.md](../docs/capability-matrix.md) and
[local-interface.md](../docs/local-interface.md).

## Not established

- Whether itsjfx has unpushed work beyond `master`.
- Why development stalled.
- Whether the Plus/Turbo behave identically to the Omni at the protocol level.

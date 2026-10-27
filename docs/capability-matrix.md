# X1 capability matrix (the roadmap)

Status of each Valetudo capability for the Ecovacs X1 in `ValetudoEV` at `master`
(code audit, 2026-10-25). This is both the honest picture of what works and the
prioritized to-do list.

Legend:
- **done**, implemented and wired for the X1
- **stub**, scaffolded as a commented-out `Mock*` registration; contract exists, no device glue
- **missing**, not present for the X1 at all
- Evidence column: what live capture is needed to implement it

## State (not capabilities, but user-visible)

| Item | Status | Notes / evidence needed |
|---|---|---|
| Battery level/flag | **done** | `EcovacsRobotStateParser` from `/robot/Robot` (local, validated); also cloud `getBattery` |
| Charge status | **done** | charge flag from `/robot/Robot` isOnCharger. Dock/station status: needs `/task/WorkState` parsing |
| Attachments (dustbin/water/mop) | partial | Declared in `getModelDetails`; live attachment state not parsed |
| **Live map** | **working end to end** | Live-fetched via `/map/GetCurrentCompressMap` (TCPROS, reflash-free), decoded by `EcovacsMapParser` (tiled LZMA1 to an 800×800 grid, floor/wall/segment layers), rendered correctly. See [map-format-decoded note](../research/map-format-decoded-2026-10-25.md). Remaining: robot/charger pose, and Node-side acquisition in the backend. |

## Priority 1, core usability

| Capability | Status | Evidence needed (capture) |
|---|---|---|
| Real map parser | **done (pending pose)** | `EcovacsMapParser` decodes the tiled CompressMap to floor/wall/segment layers; live acquisition proven via GetCurrentCompressMap. Remaining: robot/charger pose |
| `BasicControl` (start/stop/pause/home) | stub | clean start/stop/pause/return-to-dock request+ack |
| `FanSpeedControl` | stub | suction preset set/get |
| `WaterUsageControl` | stub | water-flow preset set/get |
| `OperationModeControl` (vac/mop/both) | stub | mode set/get |

## Priority 2, the Valetudo "killer" features

| Capability | Status | Evidence needed |
|---|---|---|
| `ZoneCleaning` | stub | zone-clean request (coords) |
| `MapSegmentation` (room clean) | stub | segment list + clean-segments request |
| `MapSegmentEdit` / `MapSegmentRename` | missing | split/merge/rename ops |
| `GoToLocation` | stub | go-to-point request |
| `PersistentMapControl` / `MapReset` / `PendingMapChangeHandling` | stub | map lifecycle ops |
| `CombinedVirtualRestrictions` (no-go zones/walls) | missing | restriction set/get |
| `MappingPass` | stub | mapping-run request |

## Priority 3, X1 Omni dock & extras

| Capability | Status | Evidence needed |
|---|---|---|
| `MopDockCleanManualTrigger` | stub | trigger mop-wash |
| `MopDockDryManualTrigger` | stub | trigger mop-dry |
| `AutoEmptyDockManualTrigger` | stub | trigger auto-empty |
| `AutoEmptyDockAutoEmptyControl` / `...IntervalControl` | stub / missing | auto-empty settings |
| `ConsumableMonitoring` | stub | consumable life values |
| `CurrentStatistics` / `TotalStatistics` | stub | cleaning stats |
| `Locate` | stub | "find robot" beep |
| `DoNotDisturb` | stub | DnD schedule set/get |
| `SpeakerVolumeControl` / `SpeakerTest` | stub | volume set/test |
| `VoicePackManagement` | stub | voice pack ops |
| `KeyLock` | stub | child-lock toggle |
| `ManualControl` | stub | live drive commands |
| `CarpetModeControl` / `CarpetSensorModeControl` | stub | carpet handling |
| `ObstacleAvoidanceControl` / `PetObstacleAvoidanceControl` / `CollisionAvoidantNavigationControl` | stub | AI avoidance toggles |

## Done

| Capability | Status | Notes |
|---|---|---|
| `WifiConfiguration` | **done** | `EcovacsWifiConfigurationCapability`, `wlan0` |
| `WifiScan` | **done (embedded)** | `LinuxWifiScanCapability`, only when on-robot |

> Update a row to **done** only with a captured request/response pair recorded in a
> dated `research/` note, per [CONTRIBUTING.md](../CONTRIBUTING.md).

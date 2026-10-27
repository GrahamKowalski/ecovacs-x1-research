# X1 live state stream: what the sensors report (2026-10-26)

Source: 15 min capture (`Desktop/x1/captures/session_20261026/`, not in git) with
`scripts/x1_stream.py` + `x1_pc_stream_rx.py` while handling the robot in this order:
pick up, set down, lid off, dustbin out, dustbin in, lid on, scent/vacuum attachment off,
mop plate on, start mopping, mop plate off while running, vacuum attachment on while
running, then hand-held "torture" (holding the wheels/brush). No notes were typed, so the
mapping below comes from the timestamps and the order.

## Attachments (all in `/robot/Robot`, mirrored in `/onOffInfo/OnOffInfo`)

| Field | Value | Meaning (observed) |
|---|---|---|
| `dirtbox[0].value` = `onOffInfo.values[type 3].value` | 0 | dustbin in |
| | 1 | dustbin out (5 s pulse at 17:19:47 to :52; the lid alone changes nothing) |
| `waterbox[0].value` = `onOffInfo.values[type 5].value` | 4 | vacuum / scent (aromatherapy) module fitted |
| | 2 | mop plate fitted ("ultra waterbox" in the enum) |
| | 0 | nothing fitted |
| `carpet[0].value` = `values[type 4]` | 1 | carpet detected (flapped 0/1 while mopping on a rug) |
| `onOffInfo.values[type 1].value` | bitmask | cliff (down-in) sensors; 62/60 while lifted, 0 on the floor |
| `onOffInfo.values[type 2].value` | 0..3 | fall sensors; 3 while lifted |
| `onOffInfo.values[type 10].value` | 1 | unknown extra sensor (type 10 is not in the dump's enum) |

Dustbin removal also raises `/alert/Alerts` type 0 (ALERT_DIRT_BOX_STATE) state 1 and
`/alert/DirtboxAndFall` alert_type 0 while out. `/onOffInfo/MopStateReport` and
`/onOffInfo/WaterBoxStateReport` never fired; attachment presence lives in `/robot/Robot`.

Note the documented enum (`VALUE_ULTRA_WATERBOX_IS_SET = 2`) is extended on the X1:
4 = the aromatherapy/vacuum module.

## Task state (`/task/WorkState`, `/task/TaskStateReport`, `/task/TaskResult`)

- Idle: `worktype` 7 (WORK_TYPE_IDLE), `state` 0.
- Set down after a pickup: `worktype` 8 (RELOCATION) `state` 1 for ~4 s, then `TaskResult`
  type 255 result 0 and `worktype` 7. Relocation succeeded.
- Start cleaning (button): `worktype` 0 (AUTO_CLEAN), `state` 1 (RUNNING).
- Mop plate removed while running: `state` 1 -> 2 (PAUSED) within 1 s, alert type 51
  raised; robot then drove itself onto the dock (isOnCharger 1 for 30 s) and after the vacuum
  module went on, `state` 2 -> 1 and it resumed cleaning off the dock.
- `/task/TaskStateReport` tasktype 0 stateType 2 (CLEAN_AI_DETECT_TO_CONTROL_BRUSH)
  state 1/0 pulses: the AI camera toggling the brush around obstacles.
- `/task/CurrentArea` curareaid -1 idle, 0 while cleaning room 0.

## Power

`/power/ChargeState` isOnCharger 1 / chargeState 1 (NORMAL_CHARGING) on the dock,
`/power/ChargeStateCause` ChargerCause 2 when it left. Battery drops 1 % per 2 to 3 min
while mopping. `/power/Battery` and `/robot/Robot.battery` agree.

## Alerts (`/alert/Alerts`, type per `alert/AlertType`, state 1 = active)

Seen: 0 dirt box, 2 fall error (lifted), 4 side brush current error, 10/11 left/right side
brush large current, 12 fall state warning (lifted), 16 right bump repeat, 17 bump long
trigger, 20 degree no change, 25 pose no change, 27 pitch slope, 32 LDS error, 35/37/51
(beyond the dump's enum, 51 raised when the mop plate was pulled mid-run; 35/37 appear at
each lift and at task start). The hand-held tests produced brush-current and pose/bump
warnings but no "stuck" (31) or spoken alert; those are decided by higher-level logic.
The spoken alerts use a different table (`ALERT_TYPE_*` strings in `liberos.so`, e.g.
ALERT_TYPE_NO_MOP, ALERT_TYPE_ULTRABOX_INSTALL, ALERT_TYPE_AROM_INSTALL).

## Dock

`/map/ChargerDockInfo` alternates every 20 s between info 3 (GET, hasGotDock 0) and
info 1 (REPORT, hasGotDock 1, finddock = 323.78, -4058.75 mm). That matches the robot's
start pose, so the dock pose IS stored and reported; use `finddock` when `hasfindDock` is 1.

## For the fork

`EcovacsRobotStateParser` can now emit: `AttachmentStateAttribute` dustbin (`dirtbox` == 0),
mop (`waterbox` == 2), watertank (`waterbox` in {2, 4} is "something fitted"; the clean-water
tank itself lives in the station and has no robot-side sensor), `StatusStateAttribute` from
`WorkState` (7/0 idle, 0/1 cleaning, 0/2 paused, 5 returning, 8 relocating), and dock
position from `ChargerDockInfo.finddock`.

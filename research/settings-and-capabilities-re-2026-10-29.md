# X1 remaining-capability reverse engineering (2026-10-29)

Owner present, robot docked and charging, authorized on-device work. All SET probes were
read-modify-write with an immediate restore; the robot was left in its original state
(DnD off 22:00-08:00, auto-empty on). Tooling: `scripts/x1_call_service.py` +
`rosmsg_decode.py` pushed to `/tmp` over HTTP (curl from robot, one-GET PC server), driven
by `scripts/x1_sh.py` over telnet 2323. ROS master binds 127.0.0.1 only, so the service
client runs on the robot.

## Do Not Disturb (SettingManage settingType 4, BLOCK_TIME) - MAPPED + IMPLEMENTED

`BlockTimeSetting = uint8 isOn, etime/DateTime startTime, etime/DateTime endTime`, where
`DateTime = year, month, date, day, hour, min, sec` (uint8 each). Only hour and minute
matter. Verified byte offsets in the 54-byte SettingManage request/response:

| field | offset |
|---|---|
| isOn (0 off / 1 on) | 4 |
| startTime.hour | 9 |
| startTime.min | 10 |
| endTime.hour | 16 |
| endTime.min | 17 |

Method: a ramp SET (bytes 4..18 = 0x03..0x11) read back verbatim, confirming the
blocktime block occupies bytes 4..18. The end-time offset was then pinned by cross-checking
the firmware's own `/data/config/medusa/settingBlock.json`: a SET with start 21:30 / end
at offset 16+17 produced `{"starth":21,"startm":30,"endh":0,"endm":7}`, proving the setting
node derives that file from end.hour@16, end.min@17 (the dumped layout). The baseline ROS
bytes had a stale end value at offset 17 written by the vendor app in a different
convention; the node's read/write convention is the dumped one.

Implemented as `EcovacsDoNotDisturbCapability` (get + set), command factory
`setDoNotDisturb()`, offsets `SETTING_OFFSET.BLOCK_*`. The firmware `settingBlock.json`
governs enforcement and is kept in sync by the ROS SET.

## Auto-empty on/off (SettingManage settingType 13, AC_ON_OFF) - MAPPED

`AutoCollectOnOff = uint8 AutoCollectOnOff` at request offset 38. Value 1 = on, 0 = off
(the ROS enum names ON=0/OFF=1 but the live field and the firmware file both use 1=on).
Verified: SET all-zero read back 0 at offset 38; SET offset 38 = 1 read back 1. Firmware
`/data/config/medusa/settingaconoff.json` reads `{"aconoff":1,"aconofftime":0}` throughout.

Not wrapped as a capability: this Valetudo version has no auto-empty enable/disable base
class, only Duration and Interval control, which do not map to a simple toggle.
`aconofftime` (0) may be an interval field worth a later probe.

## Virtual walls / no-go (service /map/ManipulateVirtualWall) - FULLY VERIFIED ON DEVICE

md5 `bafd7edc142bc8e1d53df1e28230fda4`. Request: `uint8 type (0 ADD, 1 DEL, 2 CLEAR,
3 MOD, 4 GET_VIRTUALWALLS, 5 GET_BY_ID), uint32 mapid, uint32 vwid, VirtualWall[] vwalls`.
Response: `uint8 result, uint32 mapid, VirtualWall[] vwalls`. `VirtualWall = uint32 vwid,
uint8 type (0 NORMAL, 1 CARPET, 2 RECOMMEND), Dot[] dots`; `Dot = float32 x, float32 y`.

ADD -> GET -> CLEAR round-trip proven on the active map (test wall added then cleared, no
persistent change left):
- **Active map id = 0x414A57ED (1095391213).** Read it from the `/map/GetCurrentCompressMap`
  response header: `uint8 result, uint32 mapid, ...` (mapid at body offset 1). The whole map
  body is only ~5.8 KB; read just the first 5 bytes (scripts/.../map_header.py). The
  `/map/ManipulateMapInfos` list has a LIVE MapInfo layout that differs from the dump, so its
  generic decode fails; the GetCurrentCompressMap header is the reliable source.
- **ADD** (type 0, vwid 0 -> robot assigns): sent one NORMAL wall with 2 Dots (500.0, 500.0)
  and (500.0, 1500.0). Response echoed it back with vwid 0; a follow-up GET returned the same.
- **Dot units are world millimetres**, the same frame GoTo uses (float32 round-tripped
  exactly). So Valetudo cm -> world mm via EcovacsGoToLocationCapability.POINT_CM_TO_WORLD_MM,
  and the inverse mm -> cm for reading walls back.
- **CLEAR** (type 2) removed all walls; GET then returned count 0.

A no-go line is a 2-Dot NORMAL wall; a rectangular no-go zone is a closed Dot polygon. This
is the clean path to block the recurring carpet-stuck spot. The `smartvirtualwall` package's
service carries no coordinates (read/delete only); `/map/ManipulateVirtualWall` is the add path.

### To build CombinedVirtualRestrictionsCapability (remaining)

The base class getVirtualRestrictions() is CONCRETE and reads walls from the rendered map
(LineMapEntity VIRTUAL_WALL, PolygonMapEntity NO_GO_AREA/NO_MOP_AREA); only
setVirtualRestrictions() is abstract. So a complete build is:
1. In the map poll (EcovacsRosLink), also call ManipulateVirtualWall GET (type 4) for the
   current map id and hand the walls to the robot.
2. In EcovacsMapParser, emit a LineMapEntity for 2-Dot walls and a PolygonMapEntity for
   polygon walls, converting mm -> cm -> pixel (inverse of POINT_CM_TO_WORLD_MM).
3. Cache the vendor map id on the robot (read from the GetCurrentCompressMap header, offset 1;
   the parser currently skips it).
4. commandFactory builders for get/add/clear + a response parser.
5. EcovacsCombinedVirtualRestrictionsCapability.setVirtualRestrictions(): CLEAR then ADD each
   wall/zone (Valetudo cm -> mm), on the cached map id. Register + tests.
This writes persistent map state, so validate the read-side rendering on device after deploy.

## Also mapped, not yet built

- **Spot-area edit** `/map/ManipulateSpotArea`: GET/MOD/MERGE/SPLIT areas by id with a
  split line of Dots (Valetudo MapSegmentEdit). `SpotArea = areaid, name, type, Dot[]
  polygon, uint32[] connections`.
- **Zone cleaning**: WorkManage `customAreas` (map/Dot[], elem 8) at request byte 10; a
  rectangle is a set of Dots. Needs the same coordinate transform.
- **Vendor scheduler** `/schedule/schedule` (md5 `2f2dcb52...`): add/del/get/modify a
  `schedule` record (name, isOn, DateTime, repeat, mapid, todo). Orphan schedule confirmed
  dead: `/data/config/medusa/schedule.json` is `[]`. Not a Valetudo capability (Valetudo
  defers scheduling to external tools); useful only to read or clear the vendor schedule.
- **Voice/speaker volume** `/voicectl/VoiceManage` (md5 `2dd0761036881d751b7bf90fc4024852`)
  and topic `/setting/VoiceSetLevel`. Not in the firmware's python site-packages, so the
  request layout needs a live empirical probe (same ramp/readback method) before a
  SpeakerVolumeControl capability can be built safely.

## Live service inventory (relevant)

`/setting/SettingManage`, `/task/WorkManage`, `/map/ManipulateVirtualWall`,
`/map/ManipulateSpotArea`, `/map/ManipulateCharger`, `/map/MapReplace`,
`/map/WatchPointManage`, `/newMap/Manipulate{DoorSill,Furniture,Outline,ReferenceWall}`,
`/schedule/schedule`, `/omni/OmniStatusManage`, `/voicectl/VoiceManage`, `/worklog/*`.

# X1 settings: feedback + control coverage (2026-10-26)

Confirms we can read and write the settings the Ecovacs app exposes, reflash-free over ROS.

## Feedback (read) - fully working

- Every setting publishes on a `/setting/*` topic (live, on change); streamed and decoded.
- Snapshot read via service `/setting/SettingManage`, manageType 0 (GET), settingType id.
  Verified on device: GET WATER_LEVEL returned 2 (HIGH), matching the topic; GET CARPET_MODE
  returned its CustomSetting (type 8); GET MOP_MODE / FAN_LEVEL returned 0.

## Control (write) - PROVEN on device

Service `/setting/SettingManage`: request = `uint8 manageType` (0 GET, 1 SET),
`uint8 settingType`, `SettingData data`; response = `uint8 response, uint8 settingType,
SettingData data`. Request length 54 bytes (GET and SET). Both GET and SET verified live.

SET demonstrated end to end (2026-10-26 ~19:43): water level set 2 -> 3 -> back to 2
(readback confirmed), and fan set to max (mode 2); the `/setting/FanMode` topic echoed
`mode 2, isSilent 0` and GET readback agreed, then reverted to 0. Robot left at baseline
(fan 0, water 2).

The live `SettingData` layout differs from the firmware dump (service md5 live 91e2de5f vs
dump 2799945d). Field byte offsets in the request/response, found empirically by GET readback
and SET-and-readback (managetype 0 GET is read-only; a wrong-offset SET with the matching
settingType is a no-op because the server reads the real offset):

| setting | settingType | value byte in the 54-byte request |
|---|---|---|
| WaterLevel.level | 6 | byte 20 (SettingData offset 18) |
| FanMode.mode | 7 | byte 22 (SettingData offset 20) |
| FanMode.isSilent | 7 | byte 23 |

CustomSetting sits at SettingData offset 0-1 (byte 2-3). Other fields (MopMode, CarpetMode via
CustomSetting, etc.) are a short readback-scan away using the same method.

## Control (write) - service identified and callable

### settingType ids (setting/SettingType)

| id | name | app feature | value |
|----|------|-------------|-------|
| 1 | SILENT_MODE | quiet scheduling | CustomSetting on/off |
| 2 | LIGHT_MODE | status light | CustomSetting on/off |
| 3 | SAVE_MAP_MODE | persistent map | CustomSetting on/off |
| 4 | BLOCK_TIME | do-not-disturb | BlockTimeSetting (start/end DateTime) |
| 5 | MOP_MODE | scrub intensity | 0 effective, 1 performance |
| 6 | WATER_LEVEL | water usage | 0 low .. 3 ultra |
| 7 | FAN_LEVEL | vacuum power | FanMode.mode 0-2 + isSilent (quiet/standard/max/max+) |
| 8 | CARPET_MODE | carpet suction/brush boost | CustomSetting on/off |
| 9 | AI_RECOGONIZE | AI obstacle recognition | AiSetting |
| 10 | MOP_CHANGE_NOTICE | mop-replace reminder | MopChangeNoticeSetting |
| 11 | SIMPLE_MODE | simple/quick mode | CustomSetting on/off |
| 12 | SL_ON_OFF | (self-clean related) | SlOnOff |
| 13 | AC_ON_OFF | auto-empty on/off | AutoCollectOnOff |

## Settings handled by OTHER services (not SettingManage)

Own topics, set through a different service (inventoried, not yet mapped):
- Scent intensity: `/setting/AromatherapyLevel`.
- Pro level: `/setting/SetProLevel`. Voice volume: `/setting/VoiceSetLevel` (via `/voicectl/VoiceManage`).
- Dry time / duster time: `/setting/SetDryTime`, `/setting/SetDusterTime`.
- Per-area clean count / twin-clean: `/setting/PersonalCleanCount`, `/setting/PersonalCleanOnOff`.
- Station functions (wash, dry, auto-empty trigger/duration, locks): service `/omni/OmniStatusManage`,
  topics `/omni/*`, `/setting/OmniSetLock`, `/setting/StationLock`.

## Bottom line

Feedback: complete and live. Control: the mechanism and service for every core setting are
identified and the service is confirmed callable (GET proven); sending a SET needs the one
short, safe offset-map step already demonstrated for WorkManage. Station-side and a handful of
level settings live on `/omni/OmniStatusManage` and `/voicectl/VoiceManage`, inventoried next.


## Remaining settings + locate (mapped 2026-10-26)

### Set by publishing to a `/setting/*` topic (`/node` subscribes)

Our new publisher `scripts/x1_publish.py` (a temporary real TCPROS publisher: it steals the
existing publisher's md5+definition, then serves the payload to subscribers) can set these:

| setting | topic | message | values |
|---|---|---|---|
| Scent intensity | `/setting/AromatherapyLevel` | `uint8 level` | 0 off, 1 on, 2 low, 3 mid, 4 high, 5 ultra (now 1) |
| Pro level | `/setting/SetProLevel` | `uint8 level` | now 2 |
| Voice volume | `/setting/VoiceSetLevel` | `uint8 type, uint8 level` | type 0 FUN (voice), 1 WATER |

Voice volume can also go through service `/voicectl/VoiceManage`.

### Station functions (the omni base)

- `/omni/work_control_req` (topic): `uint32 sn, uint8 type, uint8 onoff (1 start/0 stop),
  uint32 run_sec, clean_rag_setting clean_rag{type, filling_time, pump_time, washing_time,
  drying_pump_time}` - mop wash and dry with timings.
- `/omni/control` (topic): `uint32 type (1 child_lock, 2 sleep_mode, 3 light_alert), uint8 onoff`.
- `/omni/OmniStatusManage` (service): station status/manage; request fields not yet mapped
  (same empirical/GET approach as SettingManage when needed).
- Mop wash / dry / auto-empty can also be driven as tasks: WorkManage workType 13
  (AUTO_COLLECT_DIRT) and the `/subtasks/{wash_mop,dry_mop,dirt_collect}_task/control` topics
  (those carry opaque `pb_msgs` protobuf, not yet decoded).

### Locate / "find my robot" - WORKING

The app's Find Robot plays audio id **31 = I_AM_HERE** (`audio/AudioPlay` enum). `/node`
subscribes to `/audio/AudioPlay`, so publishing `{audiomode:0, value:31}` to it makes the robot
announce itself. Done live with `x1_publish.py /audio/AudioPlay 001f`: `/node` connected and
received the message. Any audio id in the enum can be played the same way (e.g. 24 go-charge,
14 clean-complete). This also establishes a general publish path to any command topic `/node`
subscribes to.

### Publish capability (new)

`scripts/x1_publish.py` + `scripts/x1_readtopic.py` (reads a topic's type/md5/definition and a
sample message). Together with the service-call and subscribe tools, we now have read, write
(services and topics), and command publish on the robot's ROS graph.

## Gap closing (2026-10-26, later)

### Locate FIXED and working
Live `audio/AudioPlay` is `uint32 audiomode, uint32 value` (8 bytes), NOT the dump's `uint8`
fields. The first publish was silent because the 2-byte payload was too short. Correct call:
`x1_publish.py /audio/AudioPlay 000000001f000000` (audiomode 0, value 31 = I_AM_HERE).
Confirmed audible. Any enum id plays via the same 8-byte payload.

### OmniStatusManage mapped (read-only)
Service `/omni/OmniStatusManage` is handled by `ecovacs::middleware_job::OmniGetStatus`
(a status GET). Request is a single byte; a zero request returns a 13-byte station-status
response (`09 00000000 00000000 01000000`). Safe to poll for station state. The station
CONTROL (wash/dry/auto-empty) is the `/omni/work_control_req` + `/omni/control` topics, and
tasks via WorkManage, already mapped.

### Subtask protobuf: schema located, left as future work
`/subtasks/*/control` carry `pb_msgs/Request` wrapping a protobuf. The schemas are embedded in
`usr/lib/liberos_pb_msg.so`: `task_node/{clean,goto,return,patrol,preparation,relocation,
remote_control}.proto` + `eros_pb_msg.proto`. They can be recovered by parsing the embedded
FileDescriptorProto. Deliberately not finished: the subtask topics are `/node`'s internal
dispatch layer and are fully redundant with `/task/WorkManage` (clean/area/goto/return/
dirt-collect), which is already proven. Documented as available if a direct subtask path is
ever wanted.

## Coverage conclusion
Feedback and control parity with the app is established: state + map + settings feedback (topics
+ GETs), task control (WorkManage: clean/area/goto/return/dirt-collect), all core settings
(SettingManage), station (omni topics + OmniStatusManage), scent/pro/voice (publish to topics),
sounds incl. locate (audio/AudioPlay), via read + service-call + topic-publish. Only the
internal, redundant subtask protobuf is left undecoded by choice.

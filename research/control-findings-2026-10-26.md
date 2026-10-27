# X1 control path: first verified commands (2026-10-26)

First commands ever sent to the robot, over its own ROS graph, reflash-free. Owner
present, robot beside them (not docked), authorized test. Tooling: `scripts/x1_call_service.py`
(raw TCPROS service client) driven from the PC via `x1_sh.py`; behaviour watched live with
`x1_stream.py` + `x1_pc_stream_rx.py`.

## Verified: stop the current task

- Service: `/task/WorkManage` (provided by node `/node`).
- Request sent raw: `managetype = 1` (WORK_CONTROL_TYPE_STOP) followed by zero bytes,
  113 bytes total, with md5sum `*` (server skips the check and deserializes against its
  own definition; all-zero tail = workType 0 and every variable-length array empty).
- Response: ok byte 1, body `00` = WorkResponseType `WORK_TASK_RESPONSE_OK`.

Observed twice:
1. 18:29, robot wedged (it had frozen mid-run earlier, brushes spinning): response OK,
   robot spoke "task ended". ~3 min later node `/node` crashed and auto-restarted
   (`/tmp/medusa_crash_cnt.log` cnt 1). Attribution unclear in isolation.
2. 18:40, robot freshly running a healthy auto-clean (worktype 0 state 1, started from the
   physical button): response OK, and 1.2 s later `/task/WorkState` went worktype 0 -> 7
   (IDLE), state 1 -> 0. **No crash** (crash count unchanged).

Conclusion: the stop command is clean. The earlier crash correlates with the robot's
pre-existing stuck state, not the command. A healthy running task stops to IDLE at once.

## Verified: go home (and start)

Same recipe, md5 `*`, zero-padded to 113 bytes:
- **Go home:** `managetype 0` (START), byte 1 `workType 5` (RETURN). Response OK. Robot
  announced "back to station", `/task/WorkState` -> worktype 5 state 1, and it drove to the
  dock. On arrival (18:49): `/power/ChargeState` isOnCharger 0->1 chargeState 0->1,
  `/task/TaskResult` type 4 (RETURN) result 0 (TASK_SUCCESS), WorkState worktype 5->7 state
  1->0. No crash. This is the first full command-to-dock cycle and the first observed
  successful RETURN result.
- **Start auto clean:** `managetype 0`, workType 0, zero tail (used in the stop test above to
  start the run from software rather than the button would be the same request; here the run
  was button-started).

Navigation quality is the firmware's own: the robot stalled badly on carpet (minutes milling
near one spot), then crossed flat floor fast. Replacing that with our own path planning +
explicit goto waypoints is the motivation for full local control, and needs the
argument-carrying request layout plus the reflash.

Map-frame note: after being carried the robot relocalized into a shifted frame; the dock that
was near (323, -4059) pre-carry ended this session at (-3198, -8203). Dock pose is
frame-relative and resets on relocalization (matches the handoff caveat). Poses are only
comparable within one localization session.

## WorkManage request structure: mapped, not fully cracked

Probed on-device (all with managetype 1 = a no-op stop while docked, so nothing moved):

- **byte 0 = managetype, byte 1 = workType** (confirmed by behaviour: stop=1,0; go-home=0,5).
- **Minimum request = 53 bytes** (37/.../51 overrun, 53 OK). The firmware dump's layout is
  37 bytes, which is exactly why the first attempt overran.
- **byte 2 is a uint8[] count** (raising it to 1 demands one more byte), i.e. the data block
  starts right after workType with a `uint8[] ids` field.
- The response is a single byte (`uint8 response`), confirmed by the actual call.

The data block is a **newer, 4-byte-larger variant** of `task/WorkData`, not the one the robot
advertises in `/task/WorkState` (that one is 47 bytes, md5 25924571, verified canonical because
our WorkState definition reproduces the live header md5 7c5461ba exactly). Evidence: the request
minimum is 53 = 2 + 47 + 4, and a goto-shaped request built against the advertised WorkData
layout (pose at byte 30) returned `std::bad_alloc`, meaning a length-prefix landed on the wrong
bytes. So the extra 4 bytes sit inside the data block and shift everything after `ids`. This is
also why the service md5 (d269451216e234040131f0f06bb4ccc2) matches no layout built from the
advertised WorkData, and why a ~530k-combo offline md5 search found nothing.

The newer definition is not in the dump's python, not a plain string in
`libMdsRosNodeWrapper.so` / `libjob_schedule_midware.so` (the libs hold the service md5 but not
a `uint8 managetype` definition block, so field names may also differ, e.g. `type` vs
`managetype`). roscpp caught the bad_alloc without crashing the node.

### CRACKED: full request byte layout (empirical, verified on device)

Recovered with `scripts/x1_map_request.py` (robot-side walk: managetype 1 no-op, one count
byte set to 1 at a time so counts never exceed 1 and never bad_alloc; the length the server
then demands reveals each field's element size). 39 service calls, no crash.

```
byte  0      uint8   managetype        (0 start, 1 stop, 2 pause, 3 resume)
byte  1      uint8   workType          (0 auto, 1 area, 5 return, 6 goto, ...)
byte  2..5   u32 len CleanWorkData.ids            (uint8[],  elem 1)
byte  6..9   u32 len <EXTRA field, 9th heap member> (elem 1; string or uint8[], name unknown)
byte 10..13  u32 len CleanWorkData.customAreas     (map/Dot[], elem 8)
byte 14..17  u32 len CleanWorkData.cycles          (uint8[],  elem 1)
byte 18..21  f32     CleanWorkData.theta
byte 22..25  u32 len CleanWorkData.states          (uint8[],  elem 1)
byte 26..29  u32 len CleanWorkData.types           (uint8[],  elem 1)
byte 30..33  u32 len ExtraWorkData.ids             (uint8[],  elem 1)
byte 34..37  u32 len ExtraWorkData.poses           (prediction/Pose[], elem 28)
byte 38..44  RemoteMove remotes (uint8 type, uint16 lastTime, int16 v, int16 w = 7 bytes)
byte 45..48  u32     ExtraWorkData.tasktime
byte 49..52  u32 len ExtraWorkData.states          (uint8[],  elem 1)
```

Empty request (all counts 0) = 53 bytes, matching the probed minimum. The extra field at
byte 6 (one of the 9 heap members the destructor frees) is what broke every md5 guess and
shifted poses from the advertised byte 30 to byte 34; its name is still unknown but it is not
needed to send commands (we use md5 `*`).

Verified no-op (managetype 1 so nothing moved): a goto-shaped request with poses count 1 at
byte 34 parses OK (81 bytes), where the old byte-30 version bad_alloc'd; an area-clean-shaped
request with ids count 1 at byte 2 and a segment id at byte 6 parses OK (54 bytes).

### Go-to validated LIVE (real argument command)

2026-10-26 19:28: sent `managetype 0, workType 6` with a pose (812, 135, -2.571) at byte 34
to bring the robot from the dock back to the office. It undocked, drove the full span of the
map (dock at -3198,-8203 up to the office) and stopped at ~690,48, ~15 cm from the target, a
normal goto tolerance. WorkState went to worktype 6 state 1; no crash. This is the first
argument-carrying command proven on device: arbitrary (x,y,theta) navigation works.

### Ready-to-send command recipes (md5 `*`)

- **Go home:** `managetype=0, workType=5`, all counts 0 -> 53 bytes (already proven live).
- **Start auto clean:** `managetype=0, workType=0` -> 53 bytes.
- **Area clean segment N:** `managetype=0, workType=1`, ids count=1 at byte 2, id byte N at
  byte 6, rest 0 -> 54 bytes. (Multiple rooms: count=k, k id bytes, length 53+k.)
- **Go to (x,y,theta) mm/rad:** `managetype=0, workType=6`, poses count=1 at byte 34, then a
  28-byte Pose: Header(seq u32, stamp 8, frame_id len u32=0) then float32 x,y,theta -> 81 bytes.
- Stop / pause / resume: `managetype=1 / 2 / 3`, workType 0 -> 53 bytes.

### What this unlocks now vs later

- **Now, no further RE:** argument-free commands (stop, start, go-home, pause, resume) and very
  likely **area clean by segment id** (managetype 0, workType 1, `ids=[segId]` at byte 3, zero
  to 54 bytes) since `ids` is the first field and the unknown 4 bytes sit after it.
- **Needs the newer layout:** goto-by-pose and custom-zone, because `poses`/`customAreas` sit
  after the shifted region.

### Ways to finish it (in rough order of safety)

1. Disassemble `WorkManageRequest::deserialize` in `libMdsRosNodeWrapper.so` (ARM) to read the
   field order directly. Risk-free, definitive, but real RE work.
2. Live array-mapping: for each offset set a single `0x01` (never `0xFF`, to avoid bad_alloc)
   and bisect the new minimum length; the jump size reveals each array's element size and thus
   the full layout. Moderate robot risk (docked, managetype 1).
3. After the reflash, instrument the running node directly.

## Request layout still not pinned down

The live `/task/WorkManage` md5 is `d269451216e234040131f0f06bb4ccc2`, matching neither the
firmware dump's definition nor ~224k brute-forced layouts. We sidestep it with md5 `*` and a
zero-padded body: enough for argument-free commands (stop, and likely start/return), but
anything needing arguments (area clean with ids, goto with a pose) needs the real field
order. The request text is not in any firmware binary, only the md5 (in the cloud-bridge
lib). Next idea: read the generated C++ struct from the `/node` executable, or craft a
minimal request and bisect field offsets by observing which byte changes behaviour.

## Likely next commands (argument-free, same recipe)

- Start auto clean: `managetype 0` (START), workType 0, zero tail.
- Go home: `managetype 0` (START), workType 5 (RETURN), zero tail. Byte 2 = 0x05.
- Pause / resume: `managetype 2` / `3`.
Each drives the robot: test docked or with the owner beside it.

## Tooling note

`x1_stream.py` had a bug: on a transient "no publisher" (the window while `/node` restarts)
each topic thread returned and died, so monitoring went silent after the 18:32 crash until
restarted. Fixed to retry with a 3 s backoff instead.


## Segment-clean confirmed on device (2026-10-26, later)

Area-clean takes the **raw map segment value** (101..109) in CleanWorkData.ids, not a 0-based
index. Sent `managetype 0, workType 1, ids=[101]`: WorkState went worktype 1 (AREA_CLEAN)
state 1, the robot undocked and headed out; stopped and sent home, re-docked. The fork's map
parser labels segments with that same value (`segmentId: "101"`), so EcovacsMapSegmentationCapability
(parseInt of the id) is correct as written.

## Note: SettingManage SET is audible

Each /setting/SettingManage SET triggers the robot's acknowledgement sound. The earlier
~12-in-a-row "update" sound was the 11-offset mop-mode SET scan. Use read-only GET-walks when
mapping; avoid rapid SET bursts (harmless but audible).
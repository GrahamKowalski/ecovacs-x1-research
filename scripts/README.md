# X1 live-acquisition toolkit

Pure-Python tools used to pull live data off a rooted X1 over its internal ROS
(TCPROS), reflash-free. They were validated on an X1 Plus (zj2102-x3, fw 1.7.2).

The robot's rospy install is incomplete, so these speak **raw TCPROS** with stdlib only
(`socket`, `struct`, `xmlrpclib`). Robot-side scripts run with the on-device `python2`;
PC-side scripts need Python 3.

## Prerequisites

1. Root the X1 (UART, serial-derived password; see the root note).
2. Start a network shell so the robot can roam without the serial tether:
   `telnetd -l /bin/sh -p 2323` then connect PuTTY (Telnet) to `<robot-ip>:2323`.
   This is NOT persistent (lost on reboot; restart via UART). The robot's IP was
   192.168.1.93 on the home LAN.

## Running commands on the robot from the PC

`x1_sh.py` drives that telnet shell non-interactively, so the whole workflow is
scriptable from the PC:

```sh
python x1_sh.py <robot-ip> "ls /tmp; ps | grep python2" [timeout_s]
```

Background a long-running process with `(trap '' HUP; cmd > /tmp/x.log 2>&1 &)`:
the robot has no `nohup`, and a plain `&` dies when the telnet session closes.

## Getting a script onto the robot

Terminal paste has a length limit, so transfer over the network instead:
- On the robot: `nc -l -p 9001 > /tmp/<script>.py &`
- On the PC: `python x1_pc_send.py <robot-ip> 9001 <script>.py`

Verify with `md5sum` on both sides (an interrupted transfer leaves an empty file).

## Live state monitoring (the main tool)

`x1_stream.py` (robot) subscribes to any number of topics and streams every message,
plus each publisher's TCPROS header, to every connected PC client. It is read-only.
`x1_pc_stream_rx.py` (PC) decodes the messages generically from the
`message_definition` text carried in those headers and prints **only the fields that
changed**, with timestamps, so you can watch state transitions while handling the robot.

```sh
# robot (once):
(trap '' HUP; python2 /tmp/x1_stream.py 9002 /robot/Robot /power/Battery \
   /power/ChargeState /task/WorkState /task/TaskStateReport /task/TaskResult \
   /onOffInfo/MopStateReport /onOffInfo/WaterBoxStateReport /onOffInfo/OnOffInfo \
   /setting/FanMode /setting/WaterLevel /setting/MopMode /lifespan/Lifespan \
   /map/ChargerDockInfo /alert/Alerts /key/Key > /tmp/x1_stream.log 2>&1 &)
# PC:
python x1_pc_stream_rx.py <robot-ip> 9002 <logdir> [--defs <rootfs site-packages>]
```

While the receiver runs, type a note and press Enter (for example `mop removed`) to
stamp it into the log next to the state changes it caused. Output goes to
`<logdir>/stream_<ts>.log`; the raw frames of every changed message go to a `.raw`
file alongside for replay. `--once <seconds>` runs unattended for a fixed window,
`--show-all <topic>` prints a topic in full every time, `--ignore <regex>` overrides
the default noise filter (LDS scan, range sensors, motor-current flicker, headers).
Several receivers can connect at once (one unattended capture plus one interactive).
`--mute <topic>` keeps a chatty topic (the station link `/task/omnireport`) out of the
console while still recording it. From Git Bash, prefix commands with `MSYS_NO_PATHCONV=1`
or topic arguments like `/task/omnireport` get rewritten as Windows paths; PowerShell is fine.

Stream frame format: `<u32 len><f64 unix_ts><u8 kind><u16 tlen><topic><payload>`,
kind 0 = publisher header body, 1 = message body, 2 = robot-side text note.

`x1_stream_start.sh` is the canonical topic set: push it with nc and run `sh /tmp/x1_stream_start.sh`
(a telnet command line is limited to 4095 bytes, so long topic lists must go through a file).
`x1_who_publishes.py <substr>` (robot) prints the publisher/subscriber nodes of matching topics and
the provider of matching services, which tells you whether a command path is observable.

## Other scripts (run on the robot with python2)

| Script | Purpose |
|---|---|
| `x1_list_topics.py` | List all ROS topics and their types (the capability inventory) |
| `x1_tcpros_service.py` | Call any ROS service: `python2 x1_tcpros_service.py <service> <md5> <type> <mapid> [outfile]`. Use md5 `*` to skip the (stale) md5 check. Writes the raw response payload. Example (live map): `x1_tcpros_service.py /map/GetCurrentCompressMap '*' 0 0 /tmp/map.bin` |
| `x1_robot_pose.py` | Subscribe to `/robot/Robot` once, print pose and save the raw message to `/tmp/robot_msg.bin` |
| `x1_slam_meta.py` | Read `slam/SlamMap` metadata (grid size, world bounds, resolution), the map origin |

## PC-side helpers

| Script | Purpose |
|---|---|
| `rosmsg_decode.py` | Generic ROS1 message decoder from definition text (used by the receiver). Standalone: `python rosmsg_decode.py <rootfs site-packages> robot/Robot robot_msg.bin` dumps every field of a saved message |
| `x1_readtopic.py` | Robot: print a topic's type, md5, message_definition and one sample message (hex) |
| `x1_publish.py` | Robot: publish one message to a topic the robot subscribes to, e.g. locate `x1_publish.py /audio/AudioPlay 001f` (I_AM_HERE) |
| `x1_map_request.py` | Robot: empirically map a service request's byte layout via safe no-op probes |
| `x1_pc_dump_defs.py` | Save every topic type's definition text from a running stream into `<outdir>/<pkg>/<Name>.msg` |
| `x1_extract_fixtures.py` | Cut sanitized test fixtures (LDS scan stripped) for the fork out of a `.raw` capture, one message per attachment/task/dock state |
| `x1_pc_send.py` | `python x1_pc_send.py <host> <port> <file>`, send a file to a robot `nc -l` listener |
| `x1_pc_recv.py` | `python x1_pc_recv.py <host> <port> <outfile>`, pull from a robot `nc -l -p <port> < file` (pull model avoids host firewall) |

Message definitions for the state/control types live in
`research/x1-ros-msg-definitions.md` (from the firmware dump) and `research/x1-ros-defs/`
(captured live from publishers; includes types the dump lacks).

## Typical live-map fetch

```sh
# robot:
python2 /tmp/x1_tcpros_service.py /map/GetCurrentCompressMap '*' 0 0 /tmp/map.bin
nc -l -p 9000 < /tmp/map.bin
# PC:
python x1_pc_recv.py <robot-ip> 9000 map.bin
# then decode with the fork's EcovacsMapParser
```

Captures (maps, poses, stream logs) are device data / a home layout. Keep raw pulls
out of git (they live in `Desktop/x1/captures`).

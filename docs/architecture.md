# ValetudoEV architecture (as it concerns the X1)

This is an orientation to how Valetudo/ValetudoEV is structured so you know where X1
work plugs in. Source: read of `itsjfx/ValetudoEV` at the current `master`
(last code push ~2025-05-26). Treat specifics as **observed (code audit)** on that
snapshot; they may drift.

## Big picture

Valetudo is a cloud-replacement that runs **on the robot** and speaks the robot's own
local control protocol, while exposing a vendor-neutral model (state attributes,
capabilities, a map) over a REST/websocket UI and over **MQTT with Home Assistant
autodiscovery**. The robot is tricked into talking to a local endpoint instead of the
vendor cloud; Valetudo plays the role of that endpoint and translates.

## Key layers

- **Core capabilities**, `backend/lib/core/capabilities/*.js`. Vendor-neutral
  capability contracts: `BasicControlCapability` (start/stop/pause/home),
  `FanSpeedControlCapability`, `ZoneCleaningCapability`, `MapSegmentationCapability`,
  `MopDockCleanManualTriggerCapability`, etc. A robot implementation subclasses these.
- **MQTT handles**, `backend/lib/mqtt/capabilities/*MqttHandle.js`. Each maps a
  capability to MQTT topics + Home Assistant autodiscovery. **This is why HA support
  comes "for free":** implement a capability for the X1 and its MQTT handle already
  exists, so the HA entity lights up automatically.
- **Robot implementations**, `backend/lib/robots/<vendor>/<Model>ValetudoRobot.js`.
  This is where a model declares which capabilities it supports and provides the
  vendor-specific glue (polling state, parsing the map, sending commands).

## The X1 implementation today

- `backend/lib/robots/ecovacs/EcovacsX1OmniValetudoRobot.js`, the only Ecovacs robot.
- `backend/lib/robots/ecovacs/capabilities/EcovacsWifiConfigurationCapability.js`, the
  only Ecovacs-specific capability implemented.
- `backend/lib/ecovacs/Ecocloud.js`, the local endpoint the robot connects to; binds
  `127.0.0.1:443` when embedded (on-robot) else `0.0.0.0:1883`. Exposes `send(type, cmd, args)`
  and `MESSAGE_TYPES.P2P`. This is the channel every new capability will drive.

Everything else for the X1 is a commented-out `Mock*` registration, the capability
contracts exist in core, but nothing connects them to the robot. See the
[capability matrix](capability-matrix.md).

## What implementing a capability means, concretely

For capability X on the X1 you need to:

1. Find the robot's local request/response for X by **capturing live traffic** (see
   [local-interface.md](local-interface.md)).
2. Add an Ecovacs implementation subclass (or wire the existing core capability) in the
   X1 robot that translates Valetudo's call into that request via `Ecocloud.send(...)`,
   and parses the response into state attributes / map data.
3. The MQTT handle + HA autodiscovery then surfaces it with no extra work.

The **map parser** is the exception and the hardest piece: `buildMap()` currently
fabricates a map. A real one must decode the robot's map payload into Valetudo's
`ValetudoMap` (layers + entities). This is the single biggest user-visible gap.

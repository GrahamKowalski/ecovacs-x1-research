# Open questions

## Coordination / governance
1. Does itsjfx have unpushed ValetudoEV X1 work, or a reason development stopped?
2. Would itsjfx merge capability PRs, or is a (renamed) fork the realistic path?
3. Is anyone else in the Valetudo/Giese rooting community already working on X1 capabilities?

## Hardware
4. ~~Does the **X1 Plus** match the X1 Omni's board/UART/root path?~~ **Resolved:** same
   Horizon X3 / `zj2102` platform, same root path. Header is 2×4 (not the 2×8 seen on some
   other models). See [root note](root-and-firmware-dump-2026-10-25.md).
5. ~~Exact UART pad locations on the Plus.~~ **Resolved:** GND=pin6, SoC TX=pin4, RX=pin3;
   annotated in [hardware.md](../docs/hardware.md). (Still worth a labelled photo for itsjfx.)
6. Which SYSINFO fields are per-device secrets vs shared, for safe redaction? (Have a full
   SYSINFO dump now, classify its fields: `sn`, `did`, `mach_pwd`, `product_key/secret`,
   MQTT `password`, `wifi_mac` are per-device; `type`, `lb` are shared.)

## Local protocol (blocks capability work)
7. The full `getInfo` response shape, what do `getStationState` and `getStats` return?
8. ~~The **map payload** encoding.~~ **Largely resolved:** `map/ManipulateShowMap` service →
   LZMA1 (Ecovacs truncated header) → 800×800 byte grid, segments `101-109`. See
   [map-format-decoded note](map-format-decoded-2026-10-25.md). Still open: exact
   wall/floor values, grid resolution + origin, robot/charger pose (`getPos`/`onPos`).
9. Request/response for each Priority-1 capability: BasicControl, FanSpeed, WaterUsage,
   OperationMode.
10. How async state pushes arrive (does the robot publish state changes, or must we poll?).
11. Zone/segment cleaning request formats and segment identification.
12. Dock triggers (mop wash/dry, auto-empty) request formats.

## Integration
13. Minimal Home Assistant setup once capabilities exist: MQTT broker + autodiscovery +
    which map card renders Valetudo's map for this robot.
14. How to keep the robot fully offline (block `*.ecouser.net`) while ValetudoEV drives it.

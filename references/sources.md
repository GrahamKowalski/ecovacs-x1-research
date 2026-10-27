# Sources and attribution

Primary and community sources this research builds on. Credit to the original authors;
their work remains under their own licenses.

## Root / firmware (Layer 1)
- itsjfx, `ecovacs-hacking`, root, dump, persistent-SSH notes for the X1 Omni:
  https://github.com/itsjfx/ecovacs-hacking  (see `x1_omni.md`)
- Dennis Giese (dontvacuum.me), Ecovacs security research & password derivation:
  - DEF CON 32 (2024): https://dontvacuum.me/talks/DEFCON32/DEFCON32_reveng_hacking_ecovacs_robots.pdf
  - HITCON CMT 2024: https://dontvacuum.me/talks/HITCON2024/HITCON-CMT-2024_Ecovacs.pdf
  - 37C3 (2023): https://dontvacuum.me/talks/37c3-2023/37c3-vacuuming-and-mowing.pdf
  - DEF CON 31 (2023): https://media.defcon.org/DEF%20CON%2031/DEF%20CON%2031%20presentations/Dennis%20Giese%20-%20Vacuum%20robot%20security%20and%20privacy%20-%20prevent%20your%20robot%20from%20sucking%20your%20data.pdf
- Password generator (Giese): https://builder.dontvacuum.me/ecopassword.php
- privacysmarthome rooting guide:
  https://www.privacysmarthome.com/guides/how-to-root-ecovacs-robot-vacuums-for-valetudo-2026/

## Hardware spec
- robotinfo.dev X1 Omni detail: https://robotinfo.dev/detail_ecovacs.1vxt52_0.html
- robotinfo.dev Ecovacs list: https://robotinfo.dev/robotinfo_ecovacs.html

## Local-control application (Layer 2)
- ValetudoEV (itsjfx, Apache-2.0): https://github.com/itsjfx/ValetudoEV
- Valetudo (Hypfer, Apache-2.0): https://github.com/Hypfer/Valetudo, https://valetudo.cloud
- Valetudo supported robots (Ecovacs not supported):
  https://valetudo.cloud/pages/general/supported-robots/

## Ecovacs protocol references (orientation only, cross-check against live capture)
- deebot-client (DeebotUniverse): https://github.com/DeebotUniverse/client.py
- bumper (cloud replacement): https://github.com/bmartin5692/bumper

## Coverage / context
- TechCrunch on Giese DEF CON 32 findings:
  https://techcrunch.com/2024/08/09/ecovacs-home-robots-can-be-hacked-to-spy-on-their-owners-researchers-say/

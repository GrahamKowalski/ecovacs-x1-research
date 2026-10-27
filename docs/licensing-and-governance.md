# Ownership, licensing, and governance

Short version: if you finish the remaining ValetudoEV X1 work, you will **not** own
"the project" in a copyright sense. You can lead a **fork** you maintain, but it stays a
derivative work built on others' Apache-2.0 code. Here's how it actually works.

## The licenses

- **Valetudo** (Hypfer), Apache-2.0.
- **ValetudoEV** (itsjfx), Apache-2.0; itself derived from Valetudo.
- **itsjfx/ecovacs-hacking**, has its own LICENSE (plus bundled Dropbear under its
  own terms). Check per-file before reusing.

Apache-2.0 is permissive: you may use, modify, fork, redistribute, and even sell, and
you may keep your changes under a different license. In return you must keep copyright
notices and the LICENSE, preserve any `NOTICE` file, and **state the significant
changes you made**. It also grants a patent license from contributors.

## Why "90% of the effort → it's mine" doesn't follow

Copyright attaches to authorship, not to effort share. Every existing line of Valetudo
and ValetudoEV remains the copyright of whoever wrote it. Writing the remaining
capability code gives **you** copyright over **your additions only**; the result is a
**collective/derivative work**, not a transfer of the whole to you. There is no
mechanism by which contributing a lot reassigns the earlier authors' copyright to you.

So:
- You can't relicense the whole project, drop the original authors' notices, or claim
  sole authorship.
- You *can* maintain a fork, steer its direction, and be its lead maintainer, that's
  the realistic sense in which it becomes "yours."

## Three models, honestly

1. **Contribute upstream to itsjfx/ValetudoEV.** PRs merged there; itsjfx stays owner
   and maintainer. You hold copyright to your commits. Best if the project is alive and
   itsjfx is responsive, least duplicated effort, your work reaches users fastest.
   Under Apache-2.0 §5, your PR is licensed inbound = outbound (Apache-2.0) unless a CLA
   says otherwise; ValetudoEV has no CLA noted.

2. **Hard-fork ValetudoEV.** Legal under Apache-2.0. You become maintainer of your fork
   and set its direction, but you must keep their copyright/LICENSE/NOTICE and state
   your changes. It's still a derivative work, the foundation is theirs. Sensible only
   if the project is genuinely abandoned and upstream is unresponsive. **Do not use the
   "Valetudo" name** on a fork: Hypfer discourages it, and the mark isn't yours. Pick a
   distinct name to avoid confusion and trademark friction.

3. **Build your own from scratch.** Only then is it wholly yours, but you lose the
   entire framework (capability model, MQTT/HA autodiscovery, UI, map pipeline) and
   take on enormous effort. Rarely worth it here.

## Important governance realities

- **Upstream Valetudo (Hypfer) will not take Ecovacs.** The project lists no Ecovacs
  support and states it depends on researchers rooting devices. So "upstream" for this
  work means **itsjfx/ValetudoEV**, not Hypfer's Valetudo. Don't expect your capability
  code to land in mainline Valetudo.
- **ValetudoEV looks stalled** (last code push ~May 2025). Before choosing between
  models 1 and 2, contact itsjfx / the rooting community: is there unpushed work, is the
  project paused deliberately, would PRs be merged? That one conversation decides
  whether you contribute or fork, and saves you from re-deriving months of someone's
  thinking.

## Recommendation

Start with **model 1**: reproduce root, capture the protocol, and open PRs to
ValetudoEV, after a coordination message to itsjfx. Keep the option of **model 2**
(a clearly-renamed fork) in reserve only if the project is truly dead. Either way, this
research repo stays MIT and separate; it documents the work, it isn't the ValetudoEV
code itself.

*This is a practical summary, not legal advice. For anything high-stakes, check the
actual LICENSE/NOTICE files and, if needed, a lawyer.*

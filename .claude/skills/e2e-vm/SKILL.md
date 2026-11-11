---
name: e2e-vm
description: Build and run the NixOS VM test. Use when a change affects boot, login or the desktop session.
---

# VM end-to-end test

The VM recipes land in step 7 (#9), so they do not exist yet. Write their names as plain text until then.

1. Run `git add -A` so Nix sees new files.
2. Build and run the VM test with the e2e recipe from step 7.
3. On pass, report the result and the run time.
4. On failure, read the test journal first. Then read the screenshots.
5. Name the failing step and the likely cause. Do not guess past the logs.
6. File a `finding` issue when the failure is not caused by your change.

The VM needs KVM. If the host has none, say so and rely on the CI `e2e` job. Never update goldens.

---
name: visual-test
description: Run the visual desktop test and read the result. Use when a change touches the shell or desktop look.
---

# Visual test

The just e2e recipe lands in step 7 (#9), so it does not exist yet. Issue #18 tracks updating this skill.

1. Run just e2e once it exists. Until then, say the recipe is missing and stop.
2. Open the screenshots the run writes. Read each one.
3. Read the compare report. Note each size or pixel mismatch and its mask.
4. Say what differs and why, in a table.
5. Paste the result under `## Try it` in the PR.

Never update goldens. Never run just golden-update or write under `tests/golden/`. A real diff is a finding: file an issue and ask the owner.

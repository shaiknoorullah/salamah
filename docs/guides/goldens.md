---
type: guide
status: current
covers: [tests/golden/*, tests/visual/masks.toml, tools/visual/*.py]
reviewed: 2026-11-11
---

# Goldens

Update the golden screenshots. Only the owner does this. Agents never update goldens.

## Rules

- Goldens live in `tests/golden/`. Masks live in `tests/visual/masks.toml`.
- A golden changes only in a PR with the label `golden-update`.
- The gate fails a PR that changes a golden without that label. The check lands with `check_goldens` in pr-rules.
- A failing visual test is a finding. File an issue and do not update the golden.

## Update locally

1. Run `just golden-update`. It runs the VM test and copies out/*.png into `tests/golden/`.
2. Open out/contact.png and review every screenshot.
3. Commit the changed files on the PR branch.
4. Add the label `golden-update`. The `gate` check re-runs on the label.

## Update from CI

1. Open the CI run and download the artifact `e2e-out`.
2. Copy `j1-bar.png` into `tests/golden/`.
3. Review it, commit it and add the label `golden-update`.

## Compare rules

`just visual` runs `python3 -m tools.visual compare`. It fails when more than 0.1 percent of the unmasked pixels differ. A pixel differs when a channel changes by more than 10 percent.

See the [develop guide](develop.md) and the [docs index](../README.md).

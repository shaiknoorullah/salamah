---
type: guide
status: current
covers: [justfile, .githooks/*, nix/devshell.nix, shell/tests/*]
reviewed: 2026-11-05
---

# Develop

Set up the shell, run the checks and know the hook rules.

## Shell

Run `nix develop` to enter the dev shell. Run `just --list` to see every recipe.

Nix flakes see only git-tracked files. Run `git add -A` before a `nix` command that must see new files.

## Recipes

- `just hooks` sets `core.hooksPath` to the repo hooks.
- `just check-fast` runs the quick checks.
- `just check` runs the full gate locally.
- `just test` runs the Python tests, then `just test-qml`.
- `just test-qml` runs the QML tests headless.
- `just docs` runs the doc checkers and linters.
- `just e2e` builds the VM test driver, runs the desktop test into `out/`, then runs `just visual`.
- `just visual` checks out/j1-bar.png and compares it to the golden when one exists.
- `just golden-update` is for the owner only. Agents never run it. See [goldens](goldens.md).

## QML tests

The runner is `qmltestrunner` from `qt6.qtdeclarative`, which the dev shell provides. The shell sets `QML_IMPORT_PATH` so the runner finds `QtQuick.Window`.

Run `QT_QPA_PLATFORM=offscreen qmltestrunner -input shell/tests`. Tests live in `shell/tests/`.

## Lite mode

Without Nix, the hooks fall back to tools on PATH. A missing tool prints "lite mode: <tool> skipped".

## Cloud sessions

Repo hooks in the Claude settings load only when salamah is the only repo in the session. The settings file is `.claude/settings.json`.

## Agent hooks

Each hook runs as `cd "$CLAUDE_PROJECT_DIR" && python3 -m tools.agents.hooks <name>`. The code is in `tools/agents/hooks.py`.

| Hook | What it does |
|---|---|
| `guard-bash` | Denies force-push, push to main, reset --hard, `--no-verify`, merges, golden writes, bad PR bodies and bad branch names. |
| `guard-paths` | Denies edits to goldens, secrets, `flake.lock` and accepted decisions. |
| `format-file` | Formats the edited file. Never fails. |
| `session-brief` | Prints the branch, issue, milestone and doctor problems. |
| `stop-check` | Runs the fast checks before the session stops. |

A hook that gets bad input denies for the guards and passes for the rest.

## Cloud setup

Run `sh tools/cloud-setup.sh` to install `just` and warm the Nix dev shell. It always exits 0. The log is at ~/.cache/salamah/cloud-setup.log.

## Scheduled jobs

The nightly e2e reports to the issue in repo variable NIGHTLY_ISSUE. The weekly scan runs `python3 -m tools.docs issue-links` and `python3 -m tools.docs stale --since 7 --mode issues`.

## Pre-push denylist

The pre-push hook needs a denylist when the remote is public. Set `$SALAMAH_DENYLIST` or create ~/.config/salamah/denylist. Scan output never prints a matched term.

See the [layout](../reference/layout.md) and the [docs index](../README.md).

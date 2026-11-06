---
type: guide
status: current
covers: [justfile, .githooks/*, nix/devshell.nix]
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
- `just docs` runs the doc checkers and linters.

## Lite mode

Without Nix, the hooks fall back to tools on PATH. A missing tool prints "lite mode: <tool> skipped".

## Cloud sessions

Repo hooks in the Claude settings load only when salamah is the only repo in the session. Planned path: .claude/settings.json.

## Pre-push denylist

The pre-push hook needs a denylist when the remote is public. Set `$SALAMAH_DENYLIST` or create ~/.config/salamah/denylist. Scan output never prints a matched term.

See the [layout](../reference/layout.md) and the [docs index](../README.md).

---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0015. Toolchain

## Context

Contributors need one simple way to run checks.

## Decision

Use `just` as the runner with a 3-line Makefile shim, a plain flake devShell and treefmt-nix.

## Consequences

- The Makefile only forwards to `just`.
- One command formats every file type.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

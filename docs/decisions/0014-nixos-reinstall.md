---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0014. Move the PC to NixOS with a tested install

## Context

The PC runs Arch on LUKS and holds the only copy of its data.

## Decision

Move the PC to NixOS through a one-command install that is tested in a VM. The same command handles reinstalls.

## Consequences

- A verified backup gates the wipe.
- The install is rehearsed before the real run.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

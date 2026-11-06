---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0005. First content is a hello-world desktop

## Context

A small first slice proves the pipeline end to end.

## Decision

Ship the scaffold plus the `home` desktop. It boots Hyprland with a hello-world bar in a VM test. Port older modules later, one issue each, after M2.

## Consequences

- The first milestone stays small and testable.
- Ports wait until the principles exist.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

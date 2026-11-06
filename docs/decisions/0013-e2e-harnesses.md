---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0013. Harnesses for visual and end-to-end tests

## Context

A desktop needs tests that use real input and real pixels.

## Decision

Build harnesses for visual and real end-to-end tests with real input.

## Consequences

- Layers run from unit tests up to install tests.
- Goldens change only through labelled PRs.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

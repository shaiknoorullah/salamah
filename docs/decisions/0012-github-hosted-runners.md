---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0012. GitHub-hosted runners

## Context

CI needs compute without a cost.

## Decision

Use the standard GitHub-hosted runners, which are free for public repos.

## Consequences

- No self-hosted runner to maintain.
- CI budgets follow the runner limits.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

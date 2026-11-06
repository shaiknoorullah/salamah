---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0007. Issue first, everything linked

## Context

Work needs a trail from idea to merge.

## Decision

Every change starts as an issue. Every artefact links to the next, and checks enforce the links.

## Consequences

- Branches, commits and PRs all carry the issue number.
- Unlinked work fails CI.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

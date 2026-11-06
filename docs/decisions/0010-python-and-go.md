---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0010. Logic in Python and Go

## Context

Tools should run without a heavy runtime.

## Decision

Write logic in Python and Go. Use TypeScript only if unavoidable, and prefer Node-free tools.

## Consequences

- Tool code uses the Python standard library.
- M1 contains no Go or TypeScript.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

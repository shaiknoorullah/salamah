---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0011. Public hygiene

## Context

A public repo must not expose private details.

## Decision

Keep company, cluster and host names, private IPs, salary and the old personal email out of every artefact.

## Consequences

- A denylist scan guards commits, PRs and issues.
- Scan output never prints the matched term.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

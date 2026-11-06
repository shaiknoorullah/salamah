---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0009. Agents recommend, the owner decides

## Context

Agents work fast but must not own design or merges.

## Decision

Agents recommend and the owner approves design. Agents never merge, force-push, reset hard or send messages for the owner. Sonnet implements, Haiku checks and Opus 5 reviews risky work. Subagents never use Opus 5.5.

## Consequences

- Model IDs are pinned in the agent step.
- Replies give a TL;DR first, then tables and short lines.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

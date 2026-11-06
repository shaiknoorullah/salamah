---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0016. Pre-wipe backup to a remote restic repo

## Context

Data must survive the wipe and stay private.

## Decision

Send the pre-wipe backup to a remote restic repo. The repo location is given at run time and never committed.

## Consequences

- The restic password stays off this repo.
- Backups are verified before the disk is touched.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

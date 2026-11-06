---
type: decision
status: proposed
covers: []
reviewed: 2026-11-05
---

# 0018. VM tests run in CI

## Context

Spike S0 showed that free runners expose a writable KVM device. The hello-world VM test passed there.

## Decision

Set `CI_VM=yes`. Run the L2 desktop end-to-end test in CI with KVM.

## Consequences

- The `e2e` job runs in CI and M1 exits on three green nights.
- A canary watches for runners that lose KVM.

See [foundation](../explanation/foundation.md).

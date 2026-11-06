---
type: decision
status: accepted
covers: []
reviewed: 2026-11-05
---

# 0004. NixOS and all-Nix

## Context

The setup must be reproducible from one source.

## Decision

Use NixOS with one flake and a host named `home`. home-manager places dotfiles. No chezmoi and no other distros.

## Consequences

- One tool describes the whole system.
- Other distros are out of scope.

Accepted by the owner on 2026-11-05.

See [foundation](../explanation/foundation.md).

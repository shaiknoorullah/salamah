---
type: reference
status: current
covers: [tools/taxonomy.py]
reviewed: 2026-11-05
---

# Taxonomy

Every vocabulary the tools read: commit types, areas, doc types, labels and milestones.

## Vocabulary

| Name | Values |
|---|---|
| ctype | `feat` `fix` `docs` `chore` `refactor` `test` `ci` `build` `perf` |
| area | `shell` `desktop` `host` `harness` `docs` `agents` `repo` |
| doc-type | `index` `tutorial` `guide` `reference` `explanation` `decision` `philosophy` |
| doc-status | `slot` `draft` `current` `superseded` |
| decision-status | `proposed` `accepted` `superseded` |

## Labels

| Label | Dimension | Colour | Description |
|---|---|---|---|
| `bug` | `type` | `ff8a7a` | Something is broken. |
| `feature` | `type` | `8ccff1` | New capability. |
| `docs` | `type` | `a7b4bb` | Documentation change. |
| `chore` | `type` | `5a7f91` | Maintenance with no user-visible change. |
| `area:shell` | `area` | `c5d1d8` | Quickshell bar and QML. |
| `area:desktop` | `area` | `c5d1d8` | Hyprland session. |
| `area:host` | `area` | `c5d1d8` | NixOS host configuration. |
| `area:harness` | `area` | `c5d1d8` | Tests, VM and visual checks. |
| `area:docs` | `area` | `c5d1d8` | Documentation. |
| `area:agents` | `area` | `c5d1d8` | Agent rules, hooks and skills. |
| `area:repo` | `area` | `c5d1d8` | Tooling, CI and GitHub setup. |
| `p0` | `priority` | `ff8a7a` | Fix before building anything else. |
| `p1` | `priority` | `f2b04d` | Needed. |
| `p2` | `priority` | `a7b4bb` | Later. |
| `needs-human` | `state` | `f2b04d` | Waiting on the owner. |
| `blocked` | `state` | `ff8a7a` | Blocked by another issue. |
| `agent-filed` | `state` | `8ccff1` | Filed by an agent. |
| `flaky` | `state` | `f2b04d` | Test fails intermittently. |
| `no-doc-change` | `switch` | `e7edf0` | Skips the stale-docs warning. |
| `golden-update` | `switch` | `e7edf0` | Allows golden screenshot changes. |

## Commit types

| ctype | Label |
|---|---|
| `feat` | `feature` |
| `fix` | `bug` |
| `docs` | `docs` |
| `chore` | `chore` |
| `refactor` | `chore` |
| `test` | `chore` |
| `ci` | `chore` |
| `build` | `chore` |
| `perf` | `chore` |

## Milestones

| Milestone | Done when |
|---|---|
| Backlog | Permanent default. |
| M1 Foundation | Build steps 0-8 done; gate required; J1 green 3 nights (or 3 local passes when CI_VM=no). |
| M2 Principles | Philosophy, principles and goals written by the owner. |
| M3 Home on NixOS | Install test green 7 nights; the PC reinstalled. |

See the [docs index](../README.md).

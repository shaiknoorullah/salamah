---
type: reference
status: current
covers: []
reviewed: 2026-11-13
---

# Glossary

Terms this repo uses. Agents use these words and add new ones as they settle.

| Term | Meaning |
|---|---|
| Owner | The one person who approves design and merges every PR. |
| Gate | The required CI check `gate`. It sums the CI jobs for a PR. |
| Hygiene | The required status `hygiene`. It scans a PR for private data. |
| Denylist | The private list of terms the hygiene scan blocks. Never printed. |
| Golden | A reference screenshot in `tests/golden/`. Only the owner updates it. |
| J1 | The boot-to-bar journey in the VM test. |
| Slot | A doc with `status: slot`: a placeholder the owner fills later. |
| Step | One planned unit of a milestone: one issue, one branch, one PR. |
| Deviation | An approved change to the plan, recorded on the milestone tracker. |
| Lite mode | Hooks that run without Nix and skip missing tools. |

See the [reference index](README.md).

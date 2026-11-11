---
type: reference
status: current
covers: [.claude/skills/*]
reviewed: 2026-11-11
---

# Skills

Skills that agents use in this repo, and external skills the owner adopts or rejects.

## Own skills

Each skill lives in `.claude/skills/<name>/SKILL.md`.

| Skill | Job |
|---|---|
| `new-issue` | Search for a duplicate, pick the form, set labels and milestone, attach to the tracker. |
| `pick-up` | Read the issue, branch from fresh main, comment "Started". |
| `open-pr` | Run `just check`, push, open the PR with `Closes #N`. Never merges. |
| `adr-propose` | Add a proposed decision record and link it in the index. |
| `doc-new` | Add a doc from the template and link it from the indexes. |
| `visual-test` | Run the visual test and read the compare report. Never updates goldens. |
| `e2e-vm` | Build and run the VM test, then read the journal and screenshots on failure. |

The recipes behind `visual-test` and `e2e-vm` land in step 7 (#9). Issue #18 tracks updating `visual-test`.

## External

| Source | Decision | Notes |
|---|---|---|
| [superpowers](https://github.com/obra/superpowers) | Adopt at user scope | Brainstorming, writing-plans, TDD and verification. |
| [anthropics/skills](https://github.com/anthropics/skills) | Adopt at user scope | The skill-creator skill only. |
| Vendored third-party skill packs | Reject | Licences and noise. |

See the [reference index](README.md).

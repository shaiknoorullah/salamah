---
type: reference
status: current
covers: []
reviewed: 2026-11-13
---

# Agent skills config

Where the Matt Pocock skills plugin finds this repo's issue tracker and domain docs. It replaces the files `setup-matt-pocock-skills` would write.

`AGENTS.md` wins over any plugin skill. Agents re-run `setup-matt-pocock-skills` only when the owner asks.

## Issue tracker

Issues live in this repo's GitHub Issues.

- Create issues with the `new-issue` skill. It searches for duplicates and picks the issue form.
- Labels come only from the [taxonomy](taxonomy.md): one type, one or more `area:` labels and a milestone.
- There are no triage labels. `needs-human` marks an issue that waits on the owner.
- Sub-issues use GitHub's native parent link. Blocking uses GitHub's native issue dependencies.
- PRs as a request surface: no.

When a skill says "publish to the issue tracker", file an issue with `new-issue`. When it says "fetch the relevant ticket", read the issue and its comments.

Skills never create `wayfinder:*` or other labels outside the taxonomy. A planning map is a tracker issue with sub-issues, as M1 used #1.

## Domain docs

Single context.

| Skill expects | This repo uses |
|---|---|
| `GLOSSARY.md` at the root | [Glossary](glossary.md) |
| `docs/adr/` | [Decisions](../decisions/README.md), MADR. Agents write `proposed`. |

Use the glossary's terms in issues, PRs and test names. Flag any output that contradicts a decision.

## Writing skills

The owner writes philosophy, principles and goals. Skills that draft prose, such as `writing-shape` and `writing-beats`, stay out of those docs. Interview skills save only the owner's words.

See the [reference index](README.md).

---
type: explanation
status: current
covers: []
reviewed: 2026-11-05
---

# Foundation

Public summary of the foundation design the owner approved on 2026-11-05.

## Goal

The repo replaces an earlier private config repo for home use. It is done when:

- every change starts as an issue and every artefact links to the next;
- docs are terse, indexed and checked;
- visual and real end-to-end tests run headless, in CI or on the PC;
- the PC moves to NixOS and reinstalls with one command;
- agents work under the same rules as the owner.

Seventeen [decisions](../decisions/README.md) record the choices. Scope is the home machine only.

## Linking model

Anything found becomes an issue first. Search for a duplicate and comment there if one exists.

| Step | Rule |
|---|---|
| Branch | Named type, issue number, slug. |
| Commit | Subject ends with the issue number in parentheses. |
| PR | Body has an Issue section with Closes or Part of. |
| Copy | The PR gets the issue labels and milestone. |
| Merge | The owner squash-merges. Agents never merge. |
| Code | TODO and FIXME carry an issue number. |

Checks enforce each rule. The [taxonomy](../reference/taxonomy.md) holds every vocabulary: labels, commit types, areas and milestones.

The `main` ruleset requires a PR and a passing `gate` job. History stays linear and force-push is blocked.

## Milestones

| Milestone | Done when |
|---|---|
| Backlog | Permanent default. |
| M1 Foundation | Build steps 0 to 8 done and `gate` required. |
| M2 Principles | The owner wrote philosophy, principles and goals. |
| M3 Home on NixOS | Install test green for 7 nights and the PC reinstalled. |

## Docs

Docs follow Diataxis and MADR. Front matter holds type, status, covers and reviewed date.

- Every doc is in the root index and its folder README.
- Every doc links out at least once.
- Docs stay under 150 lines, and sentences under 25 words.
- Reference and slot docs are exempt from the line cap.

| Check | What it does |
|---|---|
| Doc checkers | Front matter, index, references and caps. |
| rumdl | Markdown lint. |
| Vale | Bans filler and hedge words. |
| lychee | Offline link check. |
| Stale docs | Warns when covered code changes without the doc. |

Stale docs warn in M1 and fail from M2. See [develop](../guides/develop.md) for the commands.

## Agents

Agent rules live in AGENTS.md, which is planned. CLAUDE.md will point to it.

- Agents recommend. The owner approves design.
- Agents never merge, force-push, reset hard, push to main or send messages.
- Hooks and permission denies enforce this in the harness.
- Subagents pin exact model IDs: Sonnet implements, Haiku checks, Opus 5 reviews.
- Without the dev shell, hooks print a lite mode notice.

## Public hygiene

No company, cluster or host names, private IPs, salary or old personal email appear anywhere.

- A denylist scan covers staged files, pushed ranges and PR text.
- It names the file, line and rule, never the matched term.
- Only three commit emails are allowed: the owner's GitHub noreply, an Anthropic noreply and a GitHub noreply.

## Tests

| Layer | What |
|---|---|
| L0 | Unit tests in pytest. |
| L1 | Component tests, QML offscreen and pixel checks. |
| L2 | Desktop end-to-end and visual test in a NixOS VM. |
| L3 | Install test in a VM, from M3. |

Spike S0 showed free runners give a writable KVM device. See [decision 0018](../decisions/0018-ci-vm-tests.md).

L2 boots Hyprland with a hello-world bar. It checks state with `hyprctl`, OCR and screenshots. Goldens change only in PRs labelled `golden-update`. L2 is soft until three green nights.

## Install plan

A USB image ships a tool with plan, run and capture commands. The default is a dry run.

1. Preflight lists every partition and LUKS volume on the target disk.
2. Backup sends the data to a remote restic repo given at run time.
3. Verify runs a deep check and a sample restore, then records the snapshot ID.
4. Partition runs only with that snapshot ID: ESP, LUKS2 and btrfs subvolumes.
5. Install runs `nixos-install` from the flake for host `home`.
6. Restore brings back the home directory, and home-manager moves clashing dotfiles aside.
7. First boot asks for the passphrase, logs in and runs the doctor.

After step 4, the old system is gone. A rehearsal in a VM and the verified backup mitigate that risk.

## Out of scope

- The work machine and any work fork.
- Porting older modules, until after M2.
- Shell design, until after M2.
- TPM2, Secure Boot and secrets tooling, until needed.
- Releases and changelogs.

# Agent rules

Rules for every agent that works in this repo. Read this file first.

## What this is

`salamah` is a public NixOS config for one home machine. It is one flake with host `home`.

- Home-manager places the dotfiles. There is no chezmoi and no other distro.
- The first content is a Hyprland desktop with a hello-world bar, tested in a VM.
- Logic lives in Python. TypeScript only when no equal option exists.

## Owner rules

The owner sets the design. Agents recommend and the owner approves.

- Never merge a pull request. The owner squash-merges each one.
- Never force-push, run `git reset --hard`, or push to `main`.
- Never send messages for the owner: mail, chat or any outbound tool.
- Never skip hooks with `--no-verify`.
- Never update golden screenshots. The owner updates them.
- Never edit `flake.lock` by hand or accept a decision record. Agents write `proposed`.
- Hooks in `.claude/settings.json` enforce most of these rules. Do not work around a denial.

## Issue first

Every change starts as an issue. The steps follow the [taxonomy](docs/reference/taxonomy.md).

1. Search open issues for a duplicate. Comment there if one exists.
2. File the issue with the right form: bug, task, finding or decision.
3. Set one type label, one or more `area:` labels and a milestone.
4. Branch from fresh `main` as `<ctype>/<N>-<slug>`.
5. Commit as `ctype(area): subject (#N)`, at most 72 characters.
6. Open a PR titled `ctype(area): subject`. Put `Closes #N` or `Part of #N` under `## Issue`.
7. Stop at the PR. The owner reviews and merges.

Agent-filed issues carry the `agent-filed` label and the session link.

## Commands

Run `just --list` for the full set. These recipes exist now.

| Recipe | Use |
|---|---|
| `just check-fast` | Format, lint, tests, hygiene scan and docs. Run before every commit. |
| `just check` | Nix checks, then the fast checks. Run before opening a PR. |
| `just test` | Unit tests only. |
| `just docs` | Doc checkers, rumdl, Vale and lychee. |
| `just fmt` | Format all files with treefmt. |
| `just doctor` | Report missing tools and hooks. |
| `just hooks` | Point git at `.githooks`. |

Nix flakes see only tracked files. Run `git add -A` before a `nix` command that must see new files.

## Layout

Root holds only the files listed in [layout](docs/reference/layout.md). A folder appears with its first file.

- Tools live in `tools/`, each package with its tests beside it.
- Docs live in `docs/`, indexed by [docs/README.md](docs/README.md).
- Agent config lives in `.claude/`: settings, skills and subagents.

## Docs rules

- Follow Diataxis: tutorials, guides, reference, explanation. Decisions use MADR.
- Every doc has front matter and is linked from its folder README and the docs index.
- Name only paths and recipes that exist. Write planned things as plain text.
- Prose sentences stay at 25 words or fewer. Docs stay at 150 lines or fewer.
- No filler or hedge words. Vale enforces this.
- A PR that changes behaviour updates its docs, or says `No doc change: <reason>`.
- Run `just docs` before you commit docs.

## Test layers

| Layer | What it proves |
|---|---|
| Unit | Python tool logic, run by `just test`. |
| Docs | Links, front matter and caps, run by `just docs`. |
| VM e2e | The desktop boots to the bar with real input. |
| Visual | Screenshots match goldens within masks. |

- Write the failing test first, then the code.
- Skip or quarantine a test only with a reason that names its issue, `#N`.
- A failing visual test is a finding. File an issue and never update the golden.

## Delegation and model IDs

Spawn subagents for bounded work. The main session keeps the plan and the decisions.

| Agent | Model ID | Job |
|---|---|---|
| implementer | `claude-sonnet-5-5` | Write code and docs with TDD. |
| checker | `claude-haiku-5-5` | Run commands and verify claims. |
| reviewer | `claude-opus-5` | Read-only review of risky work. |

- Pin exact IDs. Never use an alias such as `sonnet` or `inherit`.
- Never use Opus 5.5 for a subagent.
- Definitions live in `.claude/agents/`. `python3 -m tools.agents.check` verifies them.

## Replies

- Start with a TL;DR of one or two lines.
- Prefer tables over long prose. Keep lines short.
- Say what changed, what was checked and what needs a decision.
- Refer to the owner with they, them and their.

## Public hygiene

This repo is public. Nothing private may reach a file, issue, PR, commit or screenshot.

- No company, cluster or host names. No private IPs. No salary. No old personal email.
- A private denylist lives at `$SALAMAH_DENYLIST` or ~/.config/salamah/denylist. Never print it.
- Test fixtures build sensitive patterns at run time, so the repo scans clean.
- Allowed commit emails:
  - `72301805+shaiknoorullah@users.noreply.github.com`
  - `noreply@anthropic.com`
  - `noreply@github.com`
- Agent commits use the author `Claude <noreply@anthropic.com>`.

## Agent skills

The owner installed the Matt Pocock skills plugin. Its repo config is the [agent skills config](docs/reference/agent-skills.md).

- Where a plugin skill clashes with this file, this file wins.
- Re-run `setup-matt-pocock-skills` only when the owner asks.
- Terms live in the [glossary](docs/reference/glossary.md). Decisions live in `docs/decisions/`.

## Philosophy

The owner writes these three docs. Read them, and do not draft them.

- [Philosophy](docs/philosophy/philosophy.md)
- [Principles](docs/philosophy/principles.md)
- [Goals](docs/philosophy/goals.md)

## Escalation

Stop and ask when a choice belongs to the owner or a rule blocks the work.

1. File an issue with the decision form: context, options and your recommendation.
2. Add the `needs-human` label.
3. Link the issue in the PR or session, then continue with other work.

Never guess past a denial. Never ask the owner to merge around a failing check.

## Sessions

Run build sessions on environment `salamah` with this as the only repo. Hooks load only then.

- A multi-repo session skips the hooks, so the guards do not run.
- The setup script is `tools/cloud-setup.sh`. Its log is at ~/.cache/salamah/cloud-setup.log.
- Start each session by reading the brief the SessionStart hook prints.

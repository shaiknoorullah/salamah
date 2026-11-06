---
type: reference
status: current
covers: []
reviewed: 2026-11-05
---

# Layout

Paths that exist now, with their purpose. Later tasks add rows.

| Path | Purpose |
|---|---|
| `README.md` | Pitch and entry point. |
| `LICENSE` | MIT licence. |
| `SECURITY.md` | How to report a vulnerability. |
| `flake.nix` | Flake inputs and outputs. |
| `flake.lock` | Pinned flake inputs. |
| `justfile` | Command runner recipes. |
| `Makefile` | Shim that forwards to `just`. |
| `.editorconfig` | Editor formatting rules. |
| `.gitignore` | Ignored files. |
| `nix/devshell.nix` | Dev shell definition. |
| `nix/treefmt.nix` | Formatter set for `nix fmt`. |
| `nix/checks.nix` | Flake checks. |
| `.config/*` | Tool configs: gitleaks, lychee, pytest, rumdl, ruff, typos, Vale. |
| `.githooks/pre-commit` | Fast staged-file checks. |
| `.githooks/commit-msg` | Commit message rules. |
| `.githooks/pre-push` | Hygiene scan before push. |
| `tools/doctor.py` | Environment check. |
| `tools/taxonomy.py` | Reads the taxonomy tables. |
| `tools/hygiene/scan.py` | Denylist, IP, email and TODO scan. |
| `tools/hooks/commit_msg.py` | Commit-msg and identity rules. |
| `tools/docs/` | Doc checkers. |
| `tools/gh/` | GitHub client, link rules and label sync. |
| `tools/ci/` | Changed-file classifier and gate decision. |
| `.github/ISSUE_TEMPLATE/` | Issue forms: bug, task, finding, decision. |
| `.github/pull_request_template.md` | PR body headings. |
| `.github/workflows/github.yml` | Issue triage, PR labels, hygiene scan, label sync. |
| `.github/workflows/ci.yml` | CI jobs and the `gate` check. |
| `.github/rulesets/main.json` | Ruleset for `main`, imported by the owner. |
| `docs/` | These docs. |

See the [docs index](../README.md) and the [taxonomy](taxonomy.md).

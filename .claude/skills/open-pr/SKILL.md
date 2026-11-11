---
name: open-pr
description: Open the pull request for the current branch. Use when the work is done and checks pass. Never merges.
---

# Open a PR

1. Confirm the branch matches `<ctype>/<N>-<slug>` and the tree is clean.
2. Run `just check`. Fix every failure before going on.
3. Push the branch with `git push -u origin <branch>`.
4. Read `.github/pull_request_template.md`. Fill every heading.
5. Put `Closes #N` under `## Issue`. Use `Part of #N` for a partial step.
6. Add `No doc change: <reason>` when docs need no update.
7. Create the PR titled `ctype(area): subject`. Never use `--fill`.
8. Comment the PR link on the issue.

Never run `gh pr merge` or enable auto-merge. The owner squash-merges.

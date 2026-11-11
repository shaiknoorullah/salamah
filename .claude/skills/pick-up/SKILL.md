---
name: pick-up
description: Start work on an existing issue. Use when asked to implement, fix or take issue #N.
---

# Pick up an issue

1. Read the issue and its parent tracker. Note the tasks and the done-when list.
2. Confirm nobody else holds it. Check linked PRs and branches.
3. Run `git fetch origin` and check out fresh `main`.
4. Create the branch `<ctype>/<N>-<slug>` from `main`. The ctype follows the issue type.
5. Comment "Started" on the issue with the branch name.
6. Work task by task with TDD. Commit as `ctype(area): subject (#N)`.
7. When done, use the `open-pr` skill.

Work in a single-repo session so the hooks load. Never push to `main`.

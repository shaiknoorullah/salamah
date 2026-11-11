"""Weekly maintenance: update the flake lock through a bot PR, and report stale pins."""

import argparse
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import date

from tools.gh.api import GitHub
from tools.gh.trackers import FOOTER, file_issue, find_milestone

Run = Callable[[Sequence[str]], str]
LABELS = ["chore", "area:repo", "agent-filed"]
_IDENTITY = ["-c", "user.name=github-actions", "-c", "user.email=noreply@github.com"]


def update_branch(issue: int) -> str:
    return f"chore/{issue}-weekly-updates"


def update_title(day: date) -> str:
    return f"chore(repo): weekly updates {day.isoformat()}"


def _fail_push(gh: GitHub, issue: int, err: Exception) -> None:
    gh.request(
        "PATCH",
        f"/repos/{gh.repo}/issues/{issue}",
        {"state": "closed", "state_reason": "not_planned"},
    )
    body = f"The weekly update could not push its branch ({err}). Closing this issue."
    gh.request("POST", f"/repos/{gh.repo}/issues/{issue}/comments", {"body": body + FOOTER})


def run_update(gh: GitHub, day: date, run: Run) -> int | None:
    run(["nix", "flake", "update"])
    if not run(["git", "status", "--porcelain", "flake.lock"]).strip():
        return None
    title = update_title(day)
    issue = file_issue(gh, title, "Weekly `nix flake update`.", LABELS, "Backlog")
    branch = update_branch(issue)
    run(["git", "checkout", "-b", branch])
    run(["git", "add", "flake.lock"])
    run(["git", *_IDENTITY, "commit", "-m", f"{title} (#{issue})"])
    try:
        run(["git", "push", "-u", "origin", branch])
    except (subprocess.CalledProcessError, OSError) as err:
        _fail_push(gh, issue, err)
        raise
    body = f"## Issue\n\nCloses #{issue}{FOOTER}"
    pr = gh.request(
        "POST",
        f"/repos/{gh.repo}/pulls",
        {"title": title, "head": branch, "base": "main", "body": body},
    )["number"]
    gh.request("POST", f"/repos/{gh.repo}/issues/{pr}/labels", {"labels": LABELS})
    gh.request(
        "PATCH", f"/repos/{gh.repo}/issues/{pr}", {"milestone": find_milestone(gh, "Backlog")}
    )
    gh.request("POST", f"/repos/{gh.repo}/actions/workflows/ci.yml/dispatches", {"ref": branch})
    return issue


def check_actions(gh: GitHub, run: Run) -> int | None:
    run(["pinact", "run", "--update"])
    status = run(["git", "status", "--porcelain", ".github"])
    files = [line[3:] for line in status.splitlines() if line.strip()]
    if not files:
        return None
    body = "Newer pins exist for these workflow files:\n\n" + "\n".join(f"- {f}" for f in files)
    issue = file_issue(gh, "chore(repo): update pinned actions", body, LABELS, "Backlog")
    run(["git", "checkout", "--", ".github"])  # an agent updates the actions in a normal PR
    return issue


def _run(argv: Sequence[str]) -> str:
    return subprocess.run(argv, check=True, capture_output=True, text=True).stdout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.maint.update")
    parser.add_argument("cmd", choices=("update", "actions"))
    args = parser.parse_args(argv)
    gh = GitHub.from_env()
    if args.cmd == "update":
        run_update(gh, date.today(), _run)
    else:
        check_actions(gh, _run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

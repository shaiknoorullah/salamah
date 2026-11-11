from datetime import date
from subprocess import CalledProcessError

import pytest

from tools.maint import update

OPEN = "/repos/o/r/issues?state=open&labels=agent-filed"
MILES = "/repos/o/r/milestones?state=open"
DAY = date(2026, 11, 9)
TITLE = "chore(repo): weekly updates 2026-11-09"


class Log(list):
    pass


class FakeGitHub:
    repo = "o/r"

    def __init__(self, log, pages=None):
        self.log = log
        self.calls = []
        self.pages = {MILES: [{"number": 4, "title": "Backlog"}]} | (pages or {})

    def request(self, method, path, body=None, **kw):
        self.calls.append((method, path, body))
        self.log.append(("gh", method, path))
        if (method, path) == ("POST", "/repos/o/r/issues"):
            return {"number": 42}
        if (method, path) == ("POST", "/repos/o/r/pulls"):
            return {"number": 50}

    def paginate(self, path):
        self.calls.append(("PAGE", path, None))
        return iter(self.pages.get(path, []))


def fake_run(log, *, status="", fail=None):
    def run(argv):
        log.append(("run", *argv))
        if fail and argv[: len(fail)] == fail:
            raise CalledProcessError(1, argv)
        if argv[:2] == ["git", "status"]:
            return status
        return ""

    return run


def test_update_names():
    assert update.update_branch(42) == "chore/42-weekly-updates"
    assert update.update_title(DAY) == TITLE


def test_run_update_noop():
    log = Log()
    gh = FakeGitHub(log)
    assert update.run_update(gh, DAY, fake_run(log)) is None
    assert gh.calls == []
    assert [e[1:3] for e in log] == [("nix", "flake"), ("git", "status")]


def test_run_update_full_order():
    log = Log()
    gh = FakeGitHub(log)
    run = fake_run(log, status=" M flake.lock\n")
    assert update.run_update(gh, DAY, run) == 42
    seq = [e for e in log if e[0] == "run" or e[1] != "GET"]
    subject = f"{TITLE} (#42)"
    assert seq == [
        ("run", "nix", "flake", "update"),
        ("run", "git", "status", "--porcelain", "flake.lock"),
        ("gh", "POST", "/repos/o/r/issues"),
        ("run", "git", "checkout", "-b", "chore/42-weekly-updates"),
        ("run", "git", "add", "flake.lock"),
        (
            "run",
            *["git", "-c", "user.name=github-actions", "-c", "user.email=noreply@github.com"],
            *["commit", "-m", subject],
        ),
        ("run", "git", "push", "-u", "origin", "chore/42-weekly-updates"),
        ("gh", "POST", "/repos/o/r/pulls"),
        ("gh", "POST", "/repos/o/r/issues/50/labels"),
        ("gh", "PATCH", "/repos/o/r/issues/50"),
        ("gh", "POST", "/repos/o/r/actions/workflows/ci.yml/dispatches"),
    ]
    by = {(m, p): b for m, p, b in gh.calls}
    issue = by[("POST", "/repos/o/r/issues")]
    assert issue["title"] == TITLE and issue["labels"] == ["chore", "area:repo", "agent-filed"]
    pr = by[("POST", "/repos/o/r/pulls")]
    assert pr["title"] == TITLE and pr["head"] == "chore/42-weekly-updates" and pr["base"] == "main"
    assert pr["body"].startswith("## Issue\n\nCloses #42")
    assert by[("POST", "/repos/o/r/issues/50/labels")] == {
        "labels": ["chore", "area:repo", "agent-filed"]
    }
    assert by[("PATCH", "/repos/o/r/issues/50")] == {"milestone": 4}
    assert by[("POST", "/repos/o/r/actions/workflows/ci.yml/dispatches")] == {
        "ref": "chore/42-weekly-updates"
    }


def test_run_update_push_failure_closes_issue():
    log = Log()
    gh = FakeGitHub(log)
    run = fake_run(log, status=" M flake.lock\n", fail=["git", "push"])
    with pytest.raises(CalledProcessError):
        update.run_update(gh, DAY, run)
    by = {(m, p): b for m, p, b in gh.calls}
    assert by[("PATCH", "/repos/o/r/issues/42")] == {
        "state": "closed",
        "state_reason": "not_planned",
    }
    assert ("POST", "/repos/o/r/issues/42/comments") in by
    assert ("POST", "/repos/o/r/pulls") not in by


def test_check_actions_files_issue_and_reverts():
    log = Log()
    gh = FakeGitHub(log)
    run = fake_run(log, status=" M .github/workflows/ci.yml\n M .github/workflows/github.yml\n")
    assert update.check_actions(gh, run) == 42
    assert log[0] == ("run", "pinact", "run", "--update")
    assert log[-1] == ("run", "git", "checkout", "--", ".github")
    body = next(b for m, p, b in gh.calls if (m, p) == ("POST", "/repos/o/r/issues"))
    assert body["title"] == "chore(repo): update pinned actions"
    assert ".github/workflows/ci.yml" in body["body"]
    assert body["labels"] == ["chore", "area:repo", "agent-filed"]


def test_check_actions_clean():
    log = Log()
    gh = FakeGitHub(log)
    assert update.check_actions(gh, fake_run(log)) is None
    assert gh.calls == [] and ("run", "git", "checkout", "--", ".github") not in log

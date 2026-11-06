import pytest

from tools.hooks.commit_msg import check_identity, check_message, main, subject_re
from tools.taxonomy import load

TAX = load()

PASSING = [
    "feat(shell): add bar (#12)",
    "fix(repo)!: drop old flag (#3)",
    "Merge branch 'main' into feat/12-bar",
    'Revert "feat(shell): add bar (#12)"',
    "fixup! feat(shell): add bar (#12)",
    "squash! feat(shell): add bar (#12)",
    "feat(shell): add bar (#12)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
    "# comment first\nfeat(shell): add bar (#12)\n# trailing comment\n",
]

FAILING = [
    ("feat: add bar (#12)", "area"),
    ("feat(web): add bar (#12)", "unknown area 'web'"),
    ("feature(shell): add bar (#12)", "unknown type 'feature'"),
    ("feat(shell): add bar", "missing (#N)"),
    ("feat(shell): " + "x" * 60 + " (#12)", "longer than 72"),
    ("", "empty"),
]


@pytest.mark.parametrize("message", PASSING)
def test_passing_messages(message):
    assert check_message(message, TAX) == []


@pytest.mark.parametrize(("message", "phrase"), FAILING)
def test_failing_messages(message, phrase):
    errors = check_message(message, TAX)
    assert errors
    assert any(phrase in e for e in errors)


def test_long_subject_is_73_chars():
    msg = "feat(shell): " + "x" * 60 + " (#12)"
    assert len(msg) == 79
    msg73 = "feat(shell): " + "x" * 54 + " (#12)"
    assert len(msg73) == 73
    assert any("longer than 72" in e for e in check_message(msg73, TAX))
    assert check_message("feat(shell): " + "x" * 53 + " (#12)", TAX) == []


def test_subject_re_groups():
    m = subject_re(TAX).match("fix(repo)!: drop old flag (#3)")
    assert m
    assert m.group("ctype") == "fix"
    assert m.group("area") == "repo"
    assert m.group("subject") == "drop old flag"
    assert m.group("issue") == "3"


def test_identity():
    assert check_identity("noreply@anthropic.com") == []
    other = "someone" + "@" + "corp-mail.test"
    errors = check_identity(other)
    assert len(errors) == 1
    assert other not in errors[0]


def test_main_commit_msg(tmp_path, capsys):
    good = tmp_path / "good"
    good.write_text("feat(shell): add bar (#12)\n")
    assert main(["commit-msg", str(good)]) == 0
    bad = tmp_path / "bad"
    bad.write_text("bad\n")
    assert main(["commit-msg", str(bad)]) == 1
    assert capsys.readouterr().err


def test_main_identity(capsys):
    assert main(["identity", "noreply@anthropic.com"]) == 0
    other = "someone" + "@" + "corp-mail.test"
    assert main(["identity", other]) == 1
    assert other not in capsys.readouterr().err

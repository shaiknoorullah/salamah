import io
import subprocess
from pathlib import Path

import pytest

from tools.hygiene.scan import REDACTED, Finding, load_denylist, main, redact, scan_diff, scan_text

IP = "10.0." + "14.2"
TODO = "TO" + "DO: fix"
OFF_LIST = "someone" + "@" + "corp-mail.test"


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    monkeypatch.delenv("SALAMAH_DENYLIST", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")


def deny(*terms):
    pats = load_denylist({"SALAMAH_DENYLIST": ";".join(terms)}, Path("/nonexistent"))
    assert pats is not None
    return pats


def test_denylist_rule_id_not_term():
    assert scan_text("uses ACME.", "t", deny("alpha", "acme")) == [Finding("t", 1, "denylist:2")]


def test_output_never_contains_term(monkeypatch, capsys):
    monkeypatch.setenv("SALAMAH_DENYLIST", "acme")
    monkeypatch.setattr("sys.stdin", io.StringIO("we use acme here\n"))
    assert main(["--stdin", "t"]) == 1
    out = capsys.readouterr()
    assert "acme" not in (out.out + out.err).lower()
    assert "t:1: denylist:1" in out.out


def test_word_boundaries():
    assert scan_text("acmeish and xacme", "t", deny("acme")) == []


def test_env_path_and_semicolons(tmp_path):
    f = tmp_path / "deny.txt"
    f.write_text("# comment\n\n  alpha  \nacme\n")
    pats = load_denylist({"SALAMAH_DENYLIST": str(f)}, tmp_path / "none")
    assert scan_text("acme", "t", pats) == [Finding("t", 1, "denylist:2")]
    pats = load_denylist({"SALAMAH_DENYLIST": " alpha ; acme ;;"}, tmp_path / "none")
    assert scan_text("alpha", "t", pats) == [Finding("t", 1, "denylist:1")]


def test_default_file_used_without_env(tmp_path):
    d = tmp_path / "denylist"
    d.write_text("acme\n")
    assert load_denylist({}, d) is not None
    assert load_denylist({}, tmp_path / "missing") is None


def test_private_ip_and_doc_range():
    assert scan_text(f"host {IP}", "t", []) == [Finding("t", 1, "private-ip")]
    assert scan_text("host 198.51.100.12", "t", []) == []


def test_email_allowlist():
    assert scan_text(f"mail {OFF_LIST}", "t", []) == [Finding("t", 1, "email")]
    assert scan_text("noreply@anthropic.com x@example.com", "t", []) == []


def test_todo_needs_issue():
    assert scan_text(f"# {TODO}", "t", []) == [Finding("t", 1, "todo-without-issue")]
    assert scan_text("# TO" + "DO(#12): fix", "t", []) == []
    assert scan_text("the TO" + "DO marker is a word", "t", []) == []


def test_missing_denylist_required_exits_2(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("clean\n"))
    assert main(["--require-denylist", "--stdin", "t"]) == 2


def test_empty_denylist_required_exits_2(monkeypatch):
    monkeypatch.setenv("SALAMAH_DENYLIST", " ; ;")
    monkeypatch.setattr("sys.stdin", io.StringIO("clean\n"))
    assert main(["--require-denylist", "--stdin", "t"]) == 2


def test_missing_denylist_warns(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("clean\n"))
    assert main(["--stdin", "t"]) == 0
    assert "warning: no denylist; built-in rules only" in capsys.readouterr().err


def git(*args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_staged_mode_scans_added_lines(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SALAMAH_DENYLIST", "acme")
    git("init", "-b", "main")
    (tmp_path / "a.txt").write_text("one\ntwo\n")
    git("add", "a.txt")
    git("commit", "-m", "init")
    (tmp_path / "a.txt").write_text("one\ntwo\nacme three\n")
    (tmp_path / "bin.dat").write_bytes(b"acme\x00acme")
    git("add", "a.txt", "bin.dat")
    assert main(["--staged"]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out == ["a.txt:3: denylist:1"]


def test_range_scans_commit_messages(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SALAMAH_DENYLIST", "acme")
    git("init", "-b", "main")
    (tmp_path / "a.txt").write_text("one\n")
    git("add", "a.txt")
    git("commit", "-m", "init")
    (tmp_path / "a.txt").write_text("one\ntwo\n")
    git("add", "a.txt")
    git("commit", "-m", "mention acme here")
    sha = git("rev-parse", "HEAD").strip()
    assert main(["--range", "HEAD~1..HEAD"]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out == [f"commit {sha}:1: denylist:1"]


def test_repo_scan_is_clean():
    root = Path(__file__).resolve().parents[3]
    findings = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if ".git" in rel.parts or not p.is_file():
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            continue
        try:
            text = data.decode()
        except UnicodeDecodeError:
            continue
        findings += scan_text(text, str(rel), [])
    assert findings == []


def test_path_holding_term_is_redacted():
    d = deny("acme")
    diff = "+++ b/acme/x.py\n@@ -0,0 +1,2 @@\n+hello\n+" + "10.0." + "14.2\n"
    found = scan_diff(diff, d)
    assert found == [
        Finding(REDACTED, 0, "denylist:1"),
        Finding(REDACTED, 2, "private-ip"),
    ]
    assert redact([Finding("docs/acme.md", 3, "email")], d) == [Finding(REDACTED, 3, "email")]

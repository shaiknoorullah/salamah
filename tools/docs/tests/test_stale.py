import subprocess
from pathlib import Path

from tools.docs.__main__ import main
from tools.docs.model import Doc
from tools.docs.stale import stale


def mk(path: str, covers: list[str]) -> Doc:
    meta = {"covers": covers}
    return Doc(Path(path), meta, "", 1, ())


def test_stale_warns():
    docs = [mk("docs/a.md", ["tools/*.py"]), mk("docs/b.md", ["nix/*"])]
    (p,) = stale(["tools/x/y.py"], docs, False)
    assert (p.path, p.check, p.message) == ("docs/a.md", "stale", "covers tools/x/y.py")


def test_stale_suppressed():
    assert stale(["tools/x.py"], [mk("docs/a.md", ["tools/*"])], True) == []


def test_stale_doc_changed_ok():
    docs = [mk("docs/a.md", ["tools/*"])]
    assert stale(["tools/x.py", "docs/a.md"], docs, False) == []


def test_main_stale_base_modes(tmp_path, capsys):
    def git(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "noreply@example.com")
    git("config", "user.name", "t")
    (tmp_path / "docs").mkdir()
    fm = "---\ntype: guide\nstatus: current\ncovers: [src/*]\nreviewed: 2026-11-05\n---\n"
    (tmp_path / "docs" / "a.md").write_text(fm + "[x](a.md)\n")
    git("add", "-A")
    git("commit", "-qm", "one")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "f.py").write_text("x\n")
    git("add", "-A")
    assert main(["stale", "--root", str(tmp_path), "--base", "HEAD"]) == 0
    assert "::warning file=docs/a.md::stale: covers src/f.py" in capsys.readouterr().out
    assert main(["stale", "--root", str(tmp_path), "--base", "HEAD", "--mode", "fail"]) == 1


def test_main_pr_needs_gh(capsys, monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "tools.gh", None)
    monkeypatch.setitem(sys.modules, "tools.gh.api", None)
    assert main(["stale", "--pr", "1"]) == 2
    assert "needs tools.gh" in capsys.readouterr().err


def test_main_pr_uses_github(capsys, monkeypatch, tmp_path):
    import tools.gh.api as api

    class Fake:
        repo = "o/r"

        def paginate(self, path):
            assert path == "/repos/o/r/pulls/7/files"
            return iter([{"filename": "src/f.py"}])

        def request(self, method, path):
            return {"labels": [{"name": "no-doc-change"}], "body": "No doc change: tiny"}

    monkeypatch.setattr(api.GitHub, "from_env", classmethod(lambda cls: Fake()))
    assert main(["stale", "--root", str(tmp_path), "--pr", "7"]) == 0


def test_main_stale_since_files_issue(tmp_path, monkeypatch):
    def git(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "noreply@example.com")
    git("config", "user.name", "t")
    (tmp_path / "docs").mkdir()
    fm = "---\ntype: guide\nstatus: current\ncovers: [src/*]\nreviewed: 2026-11-05\n---\n"
    (tmp_path / "docs" / "a.md").write_text(fm + "x\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "f.py").write_text("1\n")
    git("add", "-A")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2020-01-01T00:00:00")
    git("commit", "-qm", "one")
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    (tmp_path / "src" / "f.py").write_text("2\n")
    git("commit", "-qam", "two")
    filed = []
    monkeypatch.setattr("tools.gh.api.GitHub.from_env", classmethod(lambda cls: "gh"))
    monkeypatch.setattr("tools.gh.trackers.file_issue", lambda *a: filed.append(a) or 1)
    args = ["stale", "--root", str(tmp_path), "--since", "7", "--mode", "issues"]
    assert main(args) == 0
    (call,) = filed
    assert call[1:2] == ("docs: stale docs",) and "docs/a.md" in call[2] and "src/f.py" in call[2]
    assert call[3:] == (["docs", "area:docs", "agent-filed"], "Backlog")

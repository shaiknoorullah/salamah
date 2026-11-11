from pathlib import Path

from tools.docs import issue_links
from tools.docs.__main__ import main
from tools.docs.model import Doc

URL = "https://github.com/shaiknoorullah/salamah/issues/"


def mk(body: str) -> Doc:
    return Doc(Path("docs/a.md"), {}, body, 5, ())


def test_issue_links_closed_needs_word():
    body = f"see [x]({URL}3) now\nsee #4 now\nsee #3, closed\nDone: {URL}3\n`#3` ok\n```\n#3\n```\n"
    states = {3: "closed", 4: "open"}
    (p,) = issue_links.check_issue_links(mk(body), states)
    assert (p.path, p.line, p.check) == ("docs/a.md", 5, "issue-links")
    assert "#3" in p.message
    bare = issue_links.check_issue_links(mk("see #3 here\nand ref/#3 or a#3"), states)
    assert [x.line for x in bare] == [5]


def test_main_issue_links(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("---\ntype: guide\n---\nsee #3 and #3 and #4\n")
    asked = []

    class Gh:
        repo = "o/r"

        def request(self, method, path, body=None):
            asked.append(path)
            return {"state": "closed" if path.endswith("/3") else "open"}

    filed = []
    monkeypatch.setattr("tools.gh.api.GitHub.from_env", classmethod(lambda cls: Gh()))
    monkeypatch.setattr("tools.gh.trackers.file_issue", lambda *a: filed.append(a) or 1)
    assert main(["issue-links", "--root", str(tmp_path)]) == 1
    assert "docs/a.md:4: issue-links" in capsys.readouterr().out
    assert sorted(asked) == ["/repos/o/r/issues/3", "/repos/o/r/issues/4"]
    assert main(["issue-links", "--root", str(tmp_path), "--file-issues"]) == 0
    (call,) = filed
    assert call[1] == "docs: links to closed issues" and "docs/a.md:4" in call[2]
    assert call[3:] == (["docs", "area:docs", "agent-filed"], "Backlog")

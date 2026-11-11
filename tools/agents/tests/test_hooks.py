import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.agents import hooks
from tools.agents.hooks import (
    format_file,
    guard_bash,
    guard_paths,
    main,
    session_brief,
    split_commands,
    stop_check,
)

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _branch(monkeypatch):
    monkeypatch.setattr(hooks, "_current_branch", lambda repo: "feat/7-agents")


def bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


DENY = [
    ("git push --force origin x", "no force-push"),
    ("git push -f origin x", "no force-push"),
    ("git push --force-with-lease origin x", "no force-push"),
    ("git push origin +x", "no force-push"),
    ("git push origin main", "no push to main"),
    ("git push origin HEAD:main", "no push to main"),
    ("git push origin HEAD:refs/heads/main", "no push to main"),
    ("env X=1 git push origin main", "no push to main"),
    ("git -C . push origin main", "no push to main"),
    ("FOO=1 sudo git push origin main", "no push to main"),
    ("bash -c 'git push -f origin x'", "no force-push"),
    ('sh -lc "echo hi && git push -f origin x"', "no force-push"),
    ("env -S 'git push -f origin x'", "no force-push"),
    ("echo ok; git push origin main", "no push to main"),
    ("git reset --hard HEAD~1", "ask the owner"),
    ("git commit --no-verify -m x", "hooks must run"),
    ("git commit -n -m x", "hooks must run"),
    ("git push --no-verify origin x", "hooks must run"),
    ("gh pr merge 3", "the owner merges"),
    ("gh api -X PUT repos/o/r/pulls/3/merge", "the owner merges"),
    ("just golden-update", "the owner updates goldens"),
    ("rm tests/golden/a.png", "the owner updates goldens"),
    ("cp x.png tests/golden/a.png", "the owner updates goldens"),
    ("mv a ./tests/golden/b", "the owner updates goldens"),
    ("echo x > tests/golden/a.txt", "the owner updates goldens"),
    ("echo x >> tests/golden/a.txt", "the owner updates goldens"),
    ("echo x | tee tests/golden/a.txt", "the owner updates goldens"),
    ("gh pr create --title t --fill", "link an issue"),
    ("gh pr create --title t -f", "link an issue"),
    ("gh pr create --title t", "link an issue"),
    ('gh pr create --title t --body "no link"', "link an issue"),
    ("gh pr create --title t --body-file missing.md", "link an issue"),
    ("git checkout -b mybranch", "branch name rule"),
    ("git switch -c feat/no-number", "branch name rule"),
    ("git branch Feat/1-x", "branch name rule"),
    ("git checkout -b wip/12-x", "branch name rule"),
]


@pytest.mark.parametrize(("command", "phrase"), DENY)
def test_guard_denies(command, phrase):
    code, text = guard_bash(bash(command), ROOT)
    assert code == 2
    assert phrase in text


def test_guard_denies_push_without_refspec_on_main(monkeypatch):
    monkeypatch.setattr(hooks, "_current_branch", lambda repo: "main")
    assert guard_bash(bash("git push"), ROOT)[0] == 2
    assert guard_bash(bash("git push origin"), ROOT)[0] == 2


def test_guard_denies_body_file_without_link(tmp_path):
    (tmp_path / "b.md").write_text("## Issue\n\nnothing\n")
    assert guard_bash(bash("gh pr create --body-file b.md"), tmp_path)[0] == 2


ALLOW = [
    "git push -u origin feat/12-bar",
    "git push",
    "git merge main",
    "git status",
    "git checkout -b feat/12-bar",
    "git switch -c fix/3-a-b",
    "git branch --list",
    "git branch -d old",
    "git branch",
    "git commit -m 'fix: not -n'",
    "ls tests/golden",
    "cat tests/golden/a.txt > /tmp/x",
    'gh pr create --title "feat(shell): add bar" --body "## Issue\\n\\nCloses #12"',
    "gh pr create --title t --body 'Part of #4'",
    'gh pr create --title t --body="Closes #4"',
    "gh pr view 3",
    "echo 'git push --force origin main'",
    "gh pr create --title t --body $'## Issue\\n\\nCloses #12'",
]


@pytest.mark.parametrize("command", ALLOW)
def test_guard_allows(command):
    assert guard_bash(bash(command), ROOT) == (0, "")


def test_guard_allows_push_without_refspec_off_main():
    assert guard_bash(bash("git push"), ROOT) == (0, "")


def test_guard_allows_body_file_with_link(tmp_path):
    (tmp_path / "b.md").write_text("## Issue\n\nCloses #12\n")
    assert guard_bash(bash("gh pr create --title t --body-file b.md"), tmp_path) == (0, "")


def test_guard_allows_quoted_multiline():
    command = (
        'gh pr create --title "feat(x): y" --body "## Issue\n\nCloses #12\n\ngit push --force"'
    )
    assert guard_bash(bash(command), ROOT) == (0, "")
    assert len(split_commands(command)) == 1


def test_guard_allows_heredoc_commit_message():
    command = "git commit -F - <<'EOF'\nfix(x): y (#1)\n\nmentions git push --force\nEOF"
    assert guard_bash(bash(command), ROOT) == (0, "")
    command = 'git commit -m "$(cat <<EOF\nmentions git reset --hard\nEOF\n)"'
    assert guard_bash(bash(command), ROOT) == (0, "")


def test_split_commands_shapes():
    assert split_commands("a b && c; d | e\nf & g") == [
        ["a", "b"],
        ["c"],
        ["d"],
        ["e"],
        ["f"],
        ["g"],
    ]
    assert split_commands("FOO=1 BAR=2 env -i X=1 git -c a=b -C d push -f") == [
        ["git", "push", "-f"]
    ]
    assert split_commands("bash -c 'x; y z'") == [["x"], ["y", "z"]]
    assert split_commands("nohup time command git status") == [["git", "status"]]
    assert split_commands("echo $'a\\nb'") == [["echo", "a\nb"]]


def test_guard_denies_on_bad_json(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert main(["guard-bash"]) == 2
    assert capsys.readouterr().err
    monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
    assert main(["guard-paths"]) == 2
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert main(["format-file"]) == 0


def test_main_prints_deny_reason_to_stderr(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(bash("gh pr merge 3"))))
    monkeypatch.chdir(ROOT)
    assert main(["guard-bash"]) == 2
    assert "the owner merges" in capsys.readouterr().err


def write(path: str, **fields) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": path, **fields}}


def test_guard_paths(tmp_path):
    repo = tmp_path
    assert guard_paths(write("tests/golden/x.png"), repo)[0] == 2
    assert guard_paths(write(str(repo / "tests/golden/x.png")), repo)[0] == 2
    assert guard_paths(write("a/../tests/golden/x.png"), repo)[0] == 2
    assert guard_paths(write("secrets/k"), repo)[0] == 2
    assert guard_paths(write("flake.lock"), repo)[0] == 2
    decision = "docs/decisions/0001-x.md"
    assert guard_paths(write(decision, content="status: accepted"), repo)[0] == 2
    assert guard_paths(write(decision, new_string="x\nstatus: accepted"), repo)[0] == 2
    assert guard_paths(write(decision, content="status: proposed"), repo) == (0, "")
    assert guard_paths(write("tools/x.py", content="status: accepted"), repo) == (0, "")
    assert guard_paths(write("/elsewhere/flake.lock"), repo) == (0, "")


def test_format_never_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(hooks.shutil, "which", lambda name: "/no/such/" + name)
    assert format_file(write(str(tmp_path / "a.py")), tmp_path) == (0, "")
    assert format_file(write("x.unknown"), tmp_path) == (0, "")
    assert format_file({}, tmp_path) == (0, "")
    monkeypatch.setattr(hooks.shutil, "which", lambda name: None)
    assert format_file(write("a.py"), tmp_path) == (0, "")


def test_format_picks_tool(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(hooks.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(hooks.shutil, "which", lambda name: "/bin/" + name)
    format_file(write("a.py"), tmp_path)
    monkeypatch.setattr(hooks.shutil, "which", lambda name: None if name == "treefmt" else "/x")
    format_file(write("a.py"), tmp_path)
    format_file(write("b.sh"), tmp_path)
    format_file(write("c.nix"), tmp_path)
    assert calls[0][:2] == ["treefmt", "a.py"]
    assert calls[1][:2] == ["ruff", "format"]
    assert calls[2][:2] == ["shfmt", "-w"]
    assert calls[3][0] == "nixfmt"


def test_stop_respects_active(tmp_path):
    def boom(repo):
        raise AssertionError("must not run")

    event = {"stop_hook_active": True, "session_id": "s"}
    assert stop_check(event, tmp_path, tmp_path, run=boom) == (0, "")


def test_stop_counter_breaks_loop(tmp_path):
    runs = []

    def failing(repo):
        runs.append(1)
        return 1, "\n".join(f"line {i}" for i in range(50))

    event = {"session_id": "s1"}
    code, text = stop_check(event, tmp_path, tmp_path, run=failing)
    assert code == 2
    assert text.splitlines()[-1] == "line 49"
    assert len(text.splitlines()) == 30
    assert stop_check(event, tmp_path, tmp_path, run=failing)[0] == 2
    assert stop_check(event, tmp_path, tmp_path, run=failing) == (0, "")
    assert len(runs) == 2
    assert stop_check(event, tmp_path, tmp_path, run=failing)[0] == 2


def test_stop_success_resets_counter(tmp_path):
    event = {"session_id": "s2"}
    stop_check(event, tmp_path, tmp_path, run=lambda r: (1, "bad"))
    assert stop_check(event, tmp_path, tmp_path, run=lambda r: (0, "")) == (0, "")
    assert not (tmp_path / "stop-s2.count").exists()


def test_brief_reads_issue_from_branch(tmp_path, monkeypatch):
    monkeypatch.setattr(hooks, "_current_branch", lambda repo: "feat/7-agents")
    monkeypatch.setattr(hooks.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError()))
    monkeypatch.setenv("HOME", str(tmp_path))
    code, text = session_brief({}, tmp_path)
    assert code == 0
    assert "branch: feat/7-agents" in text
    assert "issue: #7" in text


def test_brief_includes_milestone_and_log(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    log = tmp_path / ".cache" / "salamah" / "cloud-setup.log"
    log.parent.mkdir(parents=True)
    log.write_text("\n".join(f"l{i}" for i in range(9)))

    def fake_run(cmd, **kw):
        out = '{"milestone": {"title": "M1 Foundation"}}' if cmd[0] == "gh" else ""
        return subprocess.CompletedProcess(cmd, 0, out, "")

    monkeypatch.setattr(hooks.subprocess, "run", fake_run)
    _, text = session_brief({}, tmp_path)
    assert "milestone: M1 Foundation" in text
    assert "l8" in text
    assert "l3" not in text


def test_runs_as_module_from_repo_root():
    result = subprocess.run(
        [sys.executable, "-m", "tools.agents.hooks", "guard-bash"],
        cwd=ROOT,
        input=json.dumps(bash("gh pr merge 3")),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert "the owner merges" in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "cat > f.txt <<EOF\nhello\nEOF\ngit push --force origin x",
        "cat > f.txt <<'END'\ngit push is fine here\nEND\ngit reset --hard",
        "cat <<-EOF > f.txt\n\tbody\n\tEOF\ngh pr merge 3",
    ],
)
def test_guard_checks_commands_after_heredoc(command):
    assert guard_bash(bash(command), ROOT)[0] == 2


def test_guard_heredoc_body_stays_data():
    command = "cat > f.txt <<EOF\ngit push --force origin main\nEOF\necho done"
    assert guard_bash(bash(command), ROOT) == (0, "")

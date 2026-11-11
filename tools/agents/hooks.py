"""Claude Code hooks: guard-bash, guard-paths, format-file, session-brief, stop-check.

Run as: cd "$CLAUDE_PROJECT_DIR" && python3 -m tools.agents.hooks <name>
Module-level imports are stdlib only; tools.* is imported inside functions.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

Result = tuple[int, str]  # (exit code, text): text goes to stderr for 2, stdout for 0

_ALLOW: Result = (0, "")
_LINK = re.compile(r"(?:Closes|Part of) #\d+\b")
_FORCE = re.compile(r"^(?:--force(?:-with-lease|-if-includes)?(?:=.*)?|-[a-zA-Z]*f[a-zA-Z]*)$")
_COMMIT_N = re.compile(r"^-[a-zA-Z]*n[a-zA-Z]*$")
_WRITERS = frozenset({"cp", "mv", "rm", "tee", "install", "rsync", "ln"})
_REDIRECTS = frozenset({">", ">>", ">|", "&>", "&>>"})
_BRANCH_OTHER = frozenset(
    "-d -D --delete -m -M --move -c -C --copy -l --list -a --all -r --remotes -v -vv "
    "--show-current --contains --merged --no-merged --unset-upstream -u --edit-description "
    "--set-upstream-to --points-at".split()
)
_PROTECTED = ("tests/golden", "secrets")


def split_commands(command: str) -> list[list[str]]:
    from tools.agents.shell import split_commands as split

    return split(command)


def _current_branch(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip()


def _rel(repo: Path, path: str) -> str | None:
    """Repo-relative posix path with `..` resolved, or None when outside the repo."""
    root = os.path.realpath(repo)
    full = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    rel = os.path.relpath(full, root).replace(os.sep, "/")
    return None if rel == ".." or rel.startswith("../") else rel


def _under(repo: Path, path: str, prefix: str) -> bool:
    rel = _rel(repo, path.split("=", 1)[-1] if path.startswith("--") else path)
    return rel is not None and (rel == prefix or rel.startswith(prefix + "/"))


def _deny_push(args: list[str], repo: Path) -> str | None:
    if any(_FORCE.match(a) for a in args if a.startswith("-")):
        return "no force-push: ask the owner"
    pos = [a for a in args if not a.startswith("-")]
    refspecs = pos[1:]
    if any(r.startswith("+") for r in refspecs):
        return "no force-push: a + refspec forces the update"
    if not refspecs:
        return "no push to main; open a PR" if _current_branch(repo) == "main" else None
    for ref in refspecs:
        target = ref.split(":")[-1].removeprefix("refs/heads/")
        if target == "main":
            return "no push to main; open a PR"
    return None


def _deny_branch(name: str) -> str | None:
    from tools.taxonomy import load

    ctypes = "|".join(re.escape(c) for c in load().vocab["ctype"])
    if re.fullmatch(rf"(?:{ctypes})/\d+-[a-z0-9-]+", name):
        return None
    return f"branch name rule: '{name}' must be <ctype>/<N>-<slug> (spec section 4, taxonomy.md)"


def _option_value(args: list[str], short: str, long: str) -> str | None:
    for i, a in enumerate(args):
        if a in (short, long):
            return args[i + 1] if i + 1 < len(args) else ""
        if a.startswith(long + "="):
            return a.split("=", 1)[1]
    return None


def _deny_pr_create(args: list[str], repo: Path) -> str | None:
    msg = "link an issue: the PR body needs 'Closes #N' or 'Part of #N' (no --fill)"
    if any(a in ("--fill", "-f", "--fill-first", "--fill-verbose") for a in args):
        return msg
    body = _option_value(args, "-b", "--body")
    body_file = _option_value(args, "-F", "--body-file")
    if body_file == "-":
        return None  # stdin body cannot be inspected here
    if body_file is not None:
        try:
            body = (repo / body_file).read_text(encoding="utf-8")
        except OSError:
            return msg + f"; cannot read {body_file}"
    if body is None or not _LINK.search(body):
        return msg
    return None


def _deny_git(cmd: list[str], repo: Path) -> str | None:
    sub, args = (cmd[1] if len(cmd) > 1 else ""), cmd[2:]
    if sub == "push":
        return _deny_push(args, repo)
    if sub == "reset" and "--hard" in args:
        return "git reset --hard is destructive: ask the owner"
    if sub == "commit" and any(_COMMIT_N.match(a) for a in args):
        return "hooks must run: do not skip them with git commit -n"
    names: list[str] = []
    if sub in ("checkout", "switch"):
        flags = ("-b", "-B") if sub == "checkout" else ("-c", "-C", "--create")
        names = [args[i + 1] for i, a in enumerate(args[:-1]) if a in flags]
    elif sub == "branch" and not any(a.split("=")[0] in _BRANCH_OTHER for a in args):
        names = [a for a in args if not a.startswith("-")][:1]
    for name in names:
        if reason := _deny_branch(name):
            return reason
    return None


def _deny_command(cmd: list[str], repo: Path) -> str | None:
    name = os.path.basename(cmd[0]) if cmd else ""
    args = cmd[1:]
    if "--no-verify" in cmd:
        return "hooks must run: do not use --no-verify"
    for i, tok in enumerate(cmd[:-1]):
        if tok in _REDIRECTS and _under(repo, cmd[i + 1], "tests/golden"):
            return "the owner updates goldens: do not write under tests/golden/"
    if name in _WRITERS and any(_under(repo, a, "tests/golden") for a in args):
        return "the owner updates goldens: do not change tests/golden/"
    if name == "just" and "golden-update" in args:
        return "the owner updates goldens: do not run just golden-update"
    if name == "git":
        return _deny_git(cmd, repo)
    if name == "gh":
        if args[:2] == ["pr", "merge"] or (
            args[:1] == ["api"] and any("/merge" in a for a in args)
        ):
            return "the owner merges: do not merge pull requests"
        if args[:2] == ["pr", "create"]:
            return _deny_pr_create(args[2:], repo)
    return None


def guard_bash(event: Mapping, repo: Path) -> Result:
    for cmd in split_commands(event["tool_input"]["command"]):
        if reason := _deny_command(cmd, repo):
            return 2, reason
    return _ALLOW


def guard_paths(event: Mapping, repo: Path) -> Result:
    tool_input = event["tool_input"]
    rel = _rel(repo, tool_input["file_path"])
    if rel is None:
        return _ALLOW
    if any(rel == p or rel.startswith(p + "/") for p in _PROTECTED) or rel == "flake.lock":
        return 2, f"{rel} is protected: the owner changes it"
    text = f"{tool_input.get('new_string', '')}\n{tool_input.get('content', '')}"
    if rel.startswith("docs/decisions/") and re.search(r"status:\s*accepted", text):
        return 2, "only the owner accepts a decision: use status: proposed"
    return _ALLOW


def format_file(event: Mapping, repo: Path) -> Result:
    try:
        path = event["tool_input"]["file_path"]
        suffix = Path(path).suffix
        if shutil.which("treefmt"):
            cmd = ["treefmt", path]
        elif suffix == ".py":
            cmd = ["ruff", "format", "--config", ".config/ruff.toml", path]
        elif suffix == ".nix":
            cmd = ["nixfmt", path]
        elif suffix == ".sh":
            cmd = ["shfmt", "-w", path]
        else:
            return _ALLOW
        subprocess.run(cmd, cwd=repo, capture_output=True, timeout=30, check=False)
    except Exception:  # noqa: BLE001 - formatting must never block an edit
        pass
    return _ALLOW


def _milestone(issue: str, repo: Path) -> str | None:
    out = subprocess.run(
        ["gh", "issue", "view", issue, "--json", "milestone"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=3,
    )
    return (json.loads(out.stdout).get("milestone") or {}).get("title")


def session_brief(event: Mapping, repo: Path) -> Result:
    branch = _current_branch(repo)
    lines = [f"branch: {branch}"]
    m = re.match(r"^[a-z]+/(\d+)-", branch)
    if m:
        lines.append(f"issue: #{m.group(1)}")
        try:
            if title := _milestone(m.group(1), repo):
                lines.append(f"milestone: {title}")
        except Exception:  # noqa: BLE001 - offline or no gh: skip
            pass
    try:
        from tools.doctor import _git_config, problems

        lines += problems(shutil.which, _git_config)
    except Exception:  # noqa: BLE001
        pass
    try:
        log = Path.home() / ".cache" / "salamah" / "cloud-setup.log"
        lines += log.read_text(encoding="utf-8").splitlines()[-5:]
    except OSError:
        pass
    return 0, "\n".join(lines)


def _run_check(repo: Path) -> tuple[int, str]:
    if shutil.which("nix"):
        cmd, limit = ["nix", "develop", "-c", "just", "check-fast"], 120
    else:
        cmd, limit = [sys.executable, "-m", "pytest", "-c", ".config/pytest.ini", "tools"], 120
    try:
        out = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True, check=False, timeout=limit
        )
    except subprocess.TimeoutExpired:
        return 1, f"check timed out after {limit} s"
    except OSError as err:
        return 1, f"check could not run: {err}"
    return out.returncode, out.stdout + out.stderr


def stop_check(
    event: Mapping,
    repo: Path,
    cache: Path,
    run: Callable[[Path], tuple[int, str]] = _run_check,
) -> Result:
    if event.get("stop_hook_active"):
        return _ALLOW
    sid = re.sub(r"[^A-Za-z0-9_-]", "_", str(event.get("session_id", "unknown")))
    counter = cache / f"stop-{sid}.count"
    try:
        blocks = int(counter.read_text())
    except (OSError, ValueError):
        blocks = 0
    if blocks >= 2:
        counter.unlink(missing_ok=True)
        return _ALLOW
    code, output = run(repo)
    if code == 0:
        counter.unlink(missing_ok=True)
        return _ALLOW
    cache.mkdir(parents=True, exist_ok=True)
    counter.write_text(str(blocks + 1))
    return 2, "\n".join(output.splitlines()[-30:])


def _read_event() -> Mapping:
    text = "" if sys.stdin.isatty() else sys.stdin.read()
    event = json.loads(text) if text.strip() else {}
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
    return event


def main(argv: list[str]) -> int:
    name = argv[0] if argv else ""
    strict = name in ("guard-bash", "guard-paths")
    try:
        repo = Path.cwd()
        event = _read_event()
        if name == "guard-bash":
            code, text = guard_bash(event, repo)
        elif name == "guard-paths":
            code, text = guard_paths(event, repo)
        elif name == "format-file":
            code, text = format_file(event, repo)
        elif name == "session-brief":
            code, text = session_brief(event, repo)
        elif name == "stop-check":
            code, text = stop_check(event, repo, Path.home() / ".cache" / "salamah")
        else:
            raise ValueError(f"unknown hook '{name}'")
    except Exception as err:  # noqa: BLE001 - guards fail closed, the rest fail open
        if strict:
            print(f"hook error ({name}): {err}", file=sys.stderr)
            return 2
        return 0
    if text:
        print(text, file=sys.stderr if code == 2 else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""CLI: `check` runs every doc check; `stale` reports docs whose covered files changed."""

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from tools import taxonomy
from tools.docs.checks import check_caps, check_front_matter, check_index, check_refs
from tools.docs.issue_links import check_issue_links, numbers
from tools.docs.model import Problem, justfile_recipes, load_docs
from tools.docs.stale import stale

_REASON = re.compile(r"^No doc change:\s*\S", re.M)


def _check(root: Path) -> int:
    tax, docs, recipes = taxonomy.load(root), load_docs(root), justfile_recipes(root)
    problems: list[Problem] = check_index(docs)
    for doc in docs:
        problems += check_front_matter(doc, tax) + check_caps(doc)
        problems += check_refs(doc, root, recipes)
    for p in sorted(problems, key=lambda p: (p.path, p.line)):
        print(f"{p.path}:{p.line}: {p.check}: {p.message}")
    return 1 if problems else 0


_ISSUE_LABELS = ["docs", "area:docs", "agent-filed"]


def _file(title: str, lines: list[str]) -> None:
    from tools.gh.api import GitHub
    from tools.gh.trackers import file_issue

    file_issue(
        GitHub.from_env(), title, "\n".join(f"- {x}" for x in lines), _ISSUE_LABELS, "Backlog"
    )


def _issue_links(args: argparse.Namespace) -> int:
    from tools.gh.api import GitHub

    docs = load_docs(args.root)
    gh, states = GitHub.from_env(), {}
    for n in sorted(numbers(docs)):
        states[n] = gh.request("GET", f"/repos/{gh.repo}/issues/{n}").get("state", "")
    problems = [p for doc in docs for p in check_issue_links(doc, states)]
    lines = [f"{p.path}:{p.line}: {p.check}: {p.message}" for p in problems]
    print("\n".join(lines))
    if problems and args.file_issues:
        _file("docs: links to closed issues", lines)
    return 1 if problems and not args.file_issues else 0


def _changed(args: argparse.Namespace, root: Path) -> tuple[list[str], bool] | None:
    if args.since is not None:
        cmd = ["git", "-C", str(root), "log", f"--since={args.since} days ago"]
        out = subprocess.run(
            [*cmd, "--name-only", "--pretty=format:"], check=True, capture_output=True, text=True
        ).stdout
        return list(dict.fromkeys(out.split())), False
    if args.base:
        cmd = ["git", "-C", str(root), "diff", "--name-only", args.base]
        out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
        return out.split(), False
    try:
        from tools.gh.api import GitHub  # lazy: keeps `check` free of the client
    except ImportError:
        return None
    gh = GitHub.from_env()
    files = [f["filename"] for f in gh.paginate(f"/repos/{gh.repo}/pulls/{args.pr}/files")]
    pr = gh.request("GET", f"/repos/{gh.repo}/pulls/{args.pr}")
    labels = [lb["name"] for lb in pr.get("labels", [])]
    skip = "no-doc-change" in labels and bool(_REASON.search(pr.get("body") or ""))
    return files, skip


def _stale(args: argparse.Namespace, root: Path) -> int:
    got = _changed(args, root)
    if got is None:
        print("needs tools.gh", file=sys.stderr)
        return 2
    problems = stale(got[0], load_docs(root), got[1])
    if args.mode == "issues":
        if problems:
            _file("docs: stale docs", [f"{p.path}: {p.message}" for p in problems])
        return 0
    for p in problems:
        print(f"::warning file={p.path}::stale: {p.message}")
    return 1 if problems and args.mode == "fail" else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.docs")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("--root", type=Path, default=Path.cwd())
    st = sub.add_parser("stale")
    st.add_argument("--root", type=Path, default=Path.cwd())
    src = st.add_mutually_exclusive_group(required=True)
    src.add_argument("--base")
    src.add_argument("--pr", type=int)
    src.add_argument("--since", type=int, metavar="DAYS")
    st.add_argument("--mode", choices=("warn", "fail", "issues"), default="warn")
    il = sub.add_parser("issue-links")
    il.add_argument("--root", type=Path, default=Path.cwd())
    il.add_argument("--file-issues", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "issue-links":
        return _issue_links(args)
    return _check(args.root) if args.cmd == "check" else _stale(args, args.root)


if __name__ == "__main__":
    sys.exit(main())

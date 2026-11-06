"""CLI: `check` runs every doc check; `stale` reports docs whose covered files changed."""

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from tools import taxonomy
from tools.docs.checks import check_caps, check_front_matter, check_index, check_refs
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


def _changed(args: argparse.Namespace, root: Path) -> tuple[list[str], bool] | None:
    if args.base:
        cmd = ["git", "-C", str(root), "diff", "--name-only", args.base]
        out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
        return out.split(), False
    try:
        from tools.gh import api  # lazy: lands in step 3
    except ImportError:
        return None
    pr = api.pr_info(args.pr)  # assumed: {"files": [...], "labels": [...], "body": str}
    skip = "no-doc-change" in pr["labels"] and bool(_REASON.search(pr["body"] or ""))
    return list(pr["files"]), skip


def _stale(args: argparse.Namespace, root: Path) -> int:
    got = _changed(args, root)
    if got is None:
        print("needs tools.gh", file=sys.stderr)
        return 2
    problems = stale(got[0], load_docs(root), got[1])
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
    st.add_argument("--mode", choices=("warn", "fail"), default="warn")
    args = parser.parse_args(argv)
    return _check(args.root) if args.cmd == "check" else _stale(args, args.root)


if __name__ == "__main__":
    sys.exit(main())

"""Classify the files a change touches, so CI can skip desktop-only jobs."""

import argparse
import fnmatch
import os
import subprocess
import sys
from collections.abc import Sequence

DESKTOP_GLOBS = (
    "shell/*",
    "hosts/*",
    "modules/*",
    "tests/vm/*",
    "tests/e2e/*",
    "tests/visual/*",
    "tests/golden/*",
    "flake.nix",
    "flake.lock",
    "nix/*",
)


def classify(files: Sequence[str]) -> dict[str, bool]:
    desktop = any(fnmatch.fnmatchcase(f, g) for f in files for g in DESKTOP_GLOBS)
    return {"desktop": desktop}


def changed_files(base: str) -> list[str]:
    """Files changed since the merge base; falls back to a plain two-dot diff."""
    for spec in (f"{base}...HEAD", f"{base}..HEAD"):
        proc = subprocess.run(
            ["git", "diff", "--name-only", spec], capture_output=True, text=True, check=False
        )
        if proc.returncode == 0:
            return proc.stdout.splitlines()
    raise RuntimeError(f"git diff failed for base {base}")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.ci.changes")
    ap.add_argument("--base", required=True)
    args = ap.parse_args(argv)
    try:
        files = changed_files(args.base)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    lines = "".join(f"{k}={str(v).lower()}\n" for k, v in classify(files).items())
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(lines)
    else:
        print(lines, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

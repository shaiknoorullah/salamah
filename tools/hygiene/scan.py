"""Hygiene scanner: private terms, private IPs, stray emails and issue-less TODOs.

Output is only `source:line: rule`; matched text is never printed.
"""

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

ALLOWED_EMAILS = frozenset(
    {
        "72301805+shaiknoorullah@users.noreply.github.com",
        "noreply@anthropic.com",
        "noreply@github.com",
    }
)
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")

PRIVATE_IP = re.compile(
    r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}"
    r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
TODO = re.compile(r"\b(TODO|FIXME)\b(?!\(#\d+\))\s*:")


@dataclass(frozen=True)
class Finding:
    source: str
    line: int
    rule: str  # "denylist:<n>" | "private-ip" | "email" | "todo-without-issue"


def load_denylist(env: Mapping[str, str], default: Path) -> list[re.Pattern[str]] | None:
    value = env.get("SALAMAH_DENYLIST")
    if value is None:
        raw = default.read_text() if default.is_file() else None
        lines = raw.splitlines() if raw is not None else []
    elif Path(value).is_file():
        lines = Path(value).read_text().splitlines()
    else:
        lines = value.split(";")
    terms = [t for t in (line.strip() for line in lines) if t and not t.startswith("#")]
    if not terms:
        return None
    return [re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)", re.I) for t in terms]


def _line_rules(line: str, deny: Sequence[re.Pattern[str]]) -> list[str]:
    rules = [f"denylist:{n}" for n, pat in enumerate(deny, 1) if pat.search(line)]
    if PRIVATE_IP.search(line):
        rules.append("private-ip")
    for m in EMAIL.finditer(line):
        addr = m.group(0)
        if (
            addr not in ALLOWED_EMAILS
            and addr.rsplit("@", 1)[1].lower() not in ALLOWED_EMAIL_DOMAINS
        ):
            rules.append("email")
            break
    if TODO.search(line):
        rules.append("todo-without-issue")
    return rules


def scan_text(text: str, source: str, deny: Sequence[re.Pattern[str]]) -> list[Finding]:
    return [
        Finding(source, n, rule)
        for n, line in enumerate(text.splitlines(), 1)
        for rule in _line_rules(line, deny)
    ]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def _scan_diff(diff: str, deny: Sequence[re.Pattern[str]]) -> list[Finding]:
    findings: list[Finding] = []
    path: str | None = None
    new_line = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith("@@"):
            m = re.match(r"@@ -\S+ \+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
        elif raw.startswith("+") and path is not None:
            findings += [Finding(path, new_line, r) for r in _line_rules(raw[1:], deny)]
            new_line += 1
    return findings


def _scan_commits(rev: str, deny: Sequence[re.Pattern[str]]) -> list[Finding]:
    parts = _git("log", "--format=%H%x00%B%x00", rev).split("\0")
    findings: list[Finding] = []
    for sha, body in zip(parts[0::2], parts[1::2], strict=False):
        findings += scan_text(body, f"commit {sha.strip()}", deny)
    return findings


def _scan_path(path: str, deny: Sequence[re.Pattern[str]]) -> list[Finding]:
    p = Path(path)
    if not p.is_file():
        return []
    data = p.read_bytes()
    if b"\0" in data[:8192]:
        return []
    try:
        return scan_text(data.decode(), path, deny)
    except UnicodeDecodeError:
        return []


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.hygiene.scan")
    ap.add_argument("--require-denylist", action="store_true")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--range", metavar="REV")
    mode.add_argument("--stdin", metavar="LABEL")
    mode.add_argument("paths", nargs="*", default=[])
    args = ap.parse_args(argv)

    deny = load_denylist(os.environ, Path.home() / ".config/salamah/denylist")
    if deny is None:
        if args.require_denylist:
            print("error: no denylist found", file=sys.stderr)
            return 2
        print("warning: no denylist; built-in rules only", file=sys.stderr)
        deny = []

    if args.staged:
        findings = _scan_diff(_git("diff", "--cached", "-U0", "--no-color", "--no-ext-diff"), deny)
    elif args.range:
        diff = _git("diff", "-U0", "--no-color", "--no-ext-diff", args.range)
        findings = _scan_diff(diff, deny) + _scan_commits(args.range, deny)
    elif args.stdin is not None:
        findings = scan_text(sys.stdin.read(), args.stdin, deny)
    else:
        findings = [f for path in args.paths for f in _scan_path(path, deny)]

    for f in findings:
        print(f"{f.source}:{f.line}: {f.rule}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

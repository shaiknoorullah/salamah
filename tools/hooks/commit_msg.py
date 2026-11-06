"""Commit-message and identity checks used by the git hooks."""

import re
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.hygiene.scan import ALLOWED_EMAILS
from tools.taxonomy import Taxonomy, load

MAX_SUBJECT = 72
_PASS_PREFIXES = ("Merge ", 'Revert "', "fixup! ", "squash! ")
_HEAD = re.compile(r"^(?P<ctype>[^\s(!:]+)(?:\((?P<area>[^)]*)\))?!?: (?P<rest>.+)$")
_ISSUE = re.compile(r" \(#\d+\)$")


def subject_re(tax: Taxonomy) -> re.Pattern[str]:
    ctypes = "|".join(re.escape(c) for c in tax.vocab["ctype"])
    areas = "|".join(re.escape(a) for a in tax.vocab["area"])
    return re.compile(
        rf"^(?P<ctype>{ctypes})\((?P<area>{areas})\)!?: (?P<subject>.+) \(#(?P<issue>\d+)\)$"
    )


def check_message(message: str, tax: Taxonomy) -> list[str]:
    lines = [ln for ln in message.splitlines() if not ln.startswith("#")]
    first = lines[0] if lines else ""
    if not first.strip():
        return ["empty commit message"]
    if first.startswith(_PASS_PREFIXES):
        return []
    head = _HEAD.match(first)
    if not head:
        return ["subject must look like 'type(area): subject (#N)'"]
    errors: list[str] = []
    ctype, area = head.group("ctype"), head.group("area")
    if ctype not in tax.vocab["ctype"]:
        errors.append(f"unknown type '{ctype}' (one of: {' '.join(tax.vocab['ctype'])})")
    if area is None:
        errors.append("missing (area) after the type (one of: " + " ".join(tax.vocab["area"]) + ")")
    elif area not in tax.vocab["area"]:
        errors.append(f"unknown area '{area}' (one of: {' '.join(tax.vocab['area'])})")
    if not _ISSUE.search(first):
        errors.append("missing (#N) issue reference at the end of the subject")
    if len(first) > MAX_SUBJECT:
        errors.append(f"subject is {len(first)} characters, longer than {MAX_SUBJECT}")
    if not errors and not subject_re(tax).match(first):
        errors.append("subject must look like 'type(area): subject (#N)'")
    return errors


def check_identity(email: str) -> list[str]:
    if email in ALLOWED_EMAILS:
        return []
    return ["git user.email is not an allowed identity; use the GitHub noreply address"]


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] not in ("commit-msg", "identity"):
        print("usage: commit_msg (commit-msg <file> | identity <email>)", file=sys.stderr)
        return 2
    if args[0] == "commit-msg":
        errors = check_message(Path(args[1]).read_text(encoding="utf-8"), load())
    else:
        errors = check_identity(args[1])
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

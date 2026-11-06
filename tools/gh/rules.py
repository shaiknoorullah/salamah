"""Pure link rules and plans for labels and milestones."""

import re
import urllib.parse
from collections.abc import Mapping, Sequence

from tools.hooks.commit_msg import MAX_SUBJECT, subject_re
from tools.hygiene.scan import ALLOWED_EMAILS
from tools.taxonomy import Label, Taxonomy

_FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,}).*?(?:^[ \t]*\1[^\n]*$|\Z)", re.M | re.S)
_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.S)
_INLINE = re.compile(r"(`+)(?!`).*?(?<!`)\1", re.S)
_REF = re.compile(r"\b(Closes|Part of) #(\d+)\b")
_ISSUE_TAIL = r" \(#(?P<issue>\d+)\)$"


def find_issue_ref(body: str) -> tuple[str, int] | None:
    text = _INLINE.sub("", _COMMENT.sub("", _FENCE.sub("", body or "")))
    section = re.search(r"^## Issue[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    m = _REF.search(section.group(1)) if section else None
    return (m.group(1), int(m.group(2))) if m else None


def check_title(title: str, tax: Taxonomy) -> list[str]:
    errors: list[str] = []
    pattern = subject_re(tax).pattern.replace(_ISSUE_TAIL, "$")
    if not re.match(pattern, title) or re.search(r" \(#\d+\)$", title):
        errors.append("PR title must look like 'type(area): subject' with no (#N)")
    if len(title) > MAX_SUBJECT:
        errors.append(f"PR title is {len(title)} characters, longer than {MAX_SUBJECT}")
    return errors


def check_branch(branch: str, issue: int, tax: Taxonomy) -> list[str]:
    ctypes = "|".join(re.escape(c) for c in tax.vocab["ctype"])
    m = re.match(rf"^(?P<ctype>{ctypes})/(?P<n>\d+)-[a-z0-9-]+$", branch)
    if not m:
        return ["branch must look like 'type/N-slug'"]
    if int(m.group("n")) != issue:
        return [f"branch issue number is {m.group('n')}, expected {issue}"]
    return []


def check_commits(commits: Sequence[Mapping], issue: int, tax: Taxonomy) -> list[str]:
    errors: list[str] = []
    for c in commits:
        if len(c.get("parents", [])) > 1:
            continue
        short = c["sha"][:7]
        subject = c["commit"]["message"].split("\n", 1)[0]
        if not subject.endswith(f"(#{issue})"):
            errors.append(f"commit {short} subject must end with (#{issue})")
        for role in ("author", "committer"):
            if c["commit"][role]["email"] not in ALLOWED_EMAILS:
                errors.append(f"commit {short} {role} email not allowlisted")
    return errors


def check_issue(issue: Mapping, tax: Taxonomy) -> list[str]:
    names = {lb["name"] for lb in issue.get("labels", [])}
    types = {lb.name for lb in tax.labels if lb.dimension == "type"}
    errors: list[str] = []
    if issue.get("state") != "open":
        errors.append("linked issue is not open")
    if len(names & types) != 1:
        errors.append(f"linked issue needs exactly one type label ({' '.join(sorted(types))})")
    if not any(n.startswith("area:") for n in names):
        errors.append("linked issue needs an area: label")
    if issue.get("milestone") is None:
        errors.append("linked issue needs a milestone")
    return errors


def check_goldens(files: Sequence[str], labels: Sequence[str]) -> list[str]:
    if "golden-update" in labels:
        return []
    return [
        f"{f}: golden change needs label golden-update"
        for f in files
        if f.startswith("tests/golden/")
    ]


def form_labels(body: str, tax: Taxonomy) -> list[str]:
    types = {lb.name for lb in tax.labels if lb.dimension == "type"}
    out: list[str] = []
    for m in re.finditer(r"^###[ \t]+(.+?)[ \t]*\n(.*?)(?=^### |\Z)", body or "", re.M | re.S):
        head = m.group(1).lower()
        values = [v.strip() for v in m.group(2).split(",")]
        for v in values:
            if head == "type" and v in types:
                label = v
            elif head == "area" and v in tax.vocab["area"]:
                label = tax.area_label(v)
            else:
                continue
            if label not in out:
                out.append(label)
    return out


def plan_labels(
    existing: Sequence[Mapping], wanted: Sequence[Label], prune: bool
) -> list[tuple[str, str, dict | None]]:
    """Return (method, path, body); paths are relative to /repos/{repo}/."""
    have = {e["name"]: e for e in existing}
    plan: list[tuple[str, str, dict | None]] = []
    for lb in wanted:
        want = {"color": lb.colour, "description": lb.description}
        cur = have.get(lb.name)
        if cur is None:
            plan.append(("POST", "labels", {"name": lb.name, **want}))
        elif (cur.get("color") or "").lower() != lb.colour.lower() or (
            cur.get("description") or ""
        ) != lb.description:
            plan.append(("PATCH", f"labels/{urllib.parse.quote(lb.name, safe='')}", want))
    if prune:
        keep = {lb.name for lb in wanted}
        for name in have:
            if name not in keep:
                plan.append(("DELETE", f"labels/{urllib.parse.quote(name, safe='')}", None))
    return plan


def plan_milestones(
    existing: Sequence[Mapping], wanted: Sequence[tuple[str, str]]
) -> list[tuple[str, str, dict]]:
    """Return (method, path, body); paths are relative to /repos/{repo}/."""
    have = {e["title"]: e for e in existing}
    plan: list[tuple[str, str, dict]] = []
    for title, desc in wanted:
        cur = have.get(title)
        if cur is None:
            plan.append(
                ("POST", "milestones", {"title": title, "state": "open", "description": desc})
            )
        elif (cur.get("description") or "") != desc:
            plan.append(("PATCH", f"milestones/{cur['number']}", {"description": desc}))
    return plan

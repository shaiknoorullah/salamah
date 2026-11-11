"""Issue links: a doc that points at a closed issue is stale unless the line says so."""

import re
from collections.abc import Iterator, Mapping, Sequence

from tools.docs.model import Doc, Problem, scan_lines

_URL = re.compile(r"https://github\.com/shaiknoorullah/salamah/issues/(\d+)\b")
_BARE = re.compile(r"(?<![\w/&#])#(\d+)\b")
_CODE = re.compile(r"`[^`]*`")
_OK = re.compile(r"closed|done", re.I)


def issue_refs(doc: Doc) -> Iterator[tuple[int, int, str]]:
    """Yield (line, issue number, line text) for links and bare refs outside code."""
    for n, line in scan_lines(doc.body, doc.body_start):
        text = _CODE.sub("", line)
        for m in _URL.finditer(text):
            yield n, int(m.group(1)), line
        for m in _BARE.finditer(_URL.sub("", text)):
            yield n, int(m.group(1)), line


def check_issue_links(doc: Doc, states: Mapping[int, str]) -> list[Problem]:
    out = []
    for n, num, line in issue_refs(doc):
        if states.get(num) == "closed" and not _OK.search(line):
            out.append(Problem(doc.path.as_posix(), n, "issue-links", f"#{num} is closed"))
    return out


def numbers(docs: Sequence[Doc]) -> set[int]:
    return {num for doc in docs for _, num, _ in issue_refs(doc)}

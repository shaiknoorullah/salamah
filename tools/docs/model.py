"""Parse docs: front matter, links, fenced-code-aware line scans and prose sentences."""

import bisect
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

Meta = dict[str, str | list[str]]

_KEY = re.compile(r"^([A-Za-z][\w-]*):[ \t]*(.*)$")
_CODE = re.compile(r"`[^`]*`")
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)[^)]*\)")
_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_SPLIT = re.compile(r"(?<=[.!?])\s+")
_RECIPE = re.compile(r"^([A-Za-z_][\w-]*)(\s.*)?:")
_ASSIGN = re.compile(r"^[\w-]+\s*:?=")
ROOT_DOCS = ("README.md", "AGENTS.md")


@dataclass(frozen=True)
class Doc:
    path: Path  # relative to the repo root
    meta: Meta  # {} for README.md and AGENTS.md at the root when they have none
    body: str
    body_start: int  # 1-based line of the first body line
    links: tuple[str, ...]  # targets of [text](target) outside code
    error: tuple[int, str] | None = None  # (line, message) when front matter is malformed


@dataclass(frozen=True)
class Problem:
    path: str
    line: int
    check: str  # front-matter | index | refs | caps | stale
    message: str


def parse_front_matter(text: str) -> tuple[Meta, str, int]:
    lines = text.replace("\r\n", "\n").split("\n")
    if lines[0] != "---":
        raise ValueError("line 1: front matter must start with ---")
    meta: Meta = {}
    for i, line in enumerate(lines[1:], start=2):
        if line == "---":
            return meta, "\n".join(lines[i:]), i + 1
        m = _KEY.match(line)
        if not m:
            raise ValueError(f"line {i}: expected 'key: value', got {line!r}")
        key, value = m.group(1), m.group(2).strip()
        if key in meta:
            raise ValueError(f"line {i}: duplicate key '{key}'")
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [x.strip() for x in value[1:-1].split(",") if x.strip()]
        else:
            meta[key] = value
    raise ValueError(f"line {len(lines)}: front matter is not closed with ---")


def scan_lines(body: str, start: int = 1) -> Iterator[tuple[int, str]]:
    """Yield (line number, line) for lines outside fenced code blocks."""
    fence = ""
    for n, line in enumerate(body.split("\n"), start=start):
        mark = line.lstrip()[:3]
        if fence:
            fence = "" if mark == fence else fence
        elif mark in ("```", "~~~"):
            fence = mark
        else:
            yield n, line


def extract_links(body: str) -> tuple[str, ...]:
    return tuple(t for _, line in scan_lines(body) for t in _LINK.findall(_CODE.sub("", line)))


def load_docs(root: Path) -> list[Doc]:
    paths = [Path(n) for n in ROOT_DOCS if (root / n).is_file()]
    paths += sorted(p.relative_to(root) for p in (root / "docs").rglob("*.md"))
    docs = []
    for rel in paths:
        text = (root / rel).read_bytes().decode("utf-8").replace("\r\n", "\n")
        meta: Meta = {}
        body, start, error = text, 1, None
        if rel.parts[0] == "docs" or text.startswith("---"):
            try:
                meta, body, start = parse_front_matter(text)
            except ValueError as exc:
                line = re.match(r"line (\d+):", str(exc))
                error = (int(line.group(1)) if line else 1, str(exc).split(": ", 1)[-1])
        docs.append(Doc(rel, meta, body, start, extract_links(body), error))
    return docs


def prose_sentences(body: str) -> Iterator[tuple[int, str]]:
    """Yield (body line, sentence) for prose; inline code is collapsed to one word."""
    para: list[tuple[int, str]] = []
    in_comment = False

    def flush() -> Iterator[tuple[int, str]]:
        if para:
            text = " ".join(t for _, t in para)
            starts, pos = [], 0
            for _, t in para:
                starts.append(pos)
                pos += len(t) + 1
            offset = 0
            for sent in _SPLIT.split(text):
                offset = text.index(sent, offset)
                yield para[bisect.bisect_right(starts, offset) - 1][0], sent.strip()
                offset += len(sent)
            para.clear()

    for n, line in scan_lines(body):
        if in_comment:
            in_comment = "-->" not in line
            continue
        s = line.strip()
        if s.startswith("<!--"):
            in_comment = "-->" not in s
            continue
        if not s or s.startswith(("|", "#")):
            yield from flush()
            continue
        if _MARKER.match(line):
            yield from flush()
        para.append((n, _CODE.sub("X", _MARKER.sub("", line)).strip()))
    yield from flush()


def justfile_recipes(root: Path) -> set[str]:
    path = root / "justfile"
    if not path.is_file():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {m.group(1) for line in lines if (m := _RECIPE.match(line)) and not _ASSIGN.match(line)}

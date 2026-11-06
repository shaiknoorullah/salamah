"""Parse docs/reference/taxonomy.md, the single source of labels and vocabularies."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

_TOKEN = re.compile(r"`([^`]+)`")
_SECTIONS = ("Vocabulary", "Labels", "Commit types", "Milestones")


@dataclass(frozen=True)
class Label:
    name: str
    dimension: str
    colour: str
    description: str


@dataclass(frozen=True)
class Taxonomy:
    vocab: Mapping[str, tuple[str, ...]]
    labels: tuple[Label, ...]
    milestones: tuple[tuple[str, str], ...]
    ctype_label: Mapping[str, str]

    def area_label(self, area: str) -> str:
        return f"area:{area}"


def _tables(text: str) -> dict[str, list[list[str]]]:
    """Map each `## ` heading to its data rows, as lists of stripped cells."""
    out: dict[str, list[list[str]]] = {}
    rows: list[list[str]] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            rows = out.setdefault(line[3:].strip(), [])
        elif rows is not None and line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(cells)
    return {k: v[1:] for k, v in out.items()}  # drop each header row


def _tokens(cell: str) -> tuple[str, ...]:
    return tuple(_TOKEN.findall(cell))


def parse(text: str) -> Taxonomy:
    tables = _tables(text)
    for section in _SECTIONS:
        if section not in tables:
            raise ValueError(f"taxonomy: missing section '{section}'")
    vocab = {row[0]: _tokens(row[1]) for row in tables["Vocabulary"]}
    labels: list[Label] = []
    seen: set[str] = set()
    for row in tables["Labels"]:
        (name,), (dim,), (colour,) = _tokens(row[0]), _tokens(row[1]), _tokens(row[2])
        if name in seen:
            raise ValueError(f"taxonomy: duplicate label '{name}'")
        if not re.fullmatch(r"[0-9a-f]{6}", colour):
            raise ValueError(f"taxonomy: bad colour '{colour}' for label '{name}'")
        seen.add(name)
        labels.append(Label(name, dim, colour, row[3]))
    ctype_label = {_tokens(r[0])[0]: _tokens(r[1])[0] for r in tables["Commit types"]}
    milestones = tuple((r[0], r[1]) for r in tables["Milestones"])
    return Taxonomy(
        MappingProxyType(vocab), tuple(labels), milestones, MappingProxyType(ctype_label)
    )


def load(root: Path | None = None) -> Taxonomy:
    root = root or Path(__file__).resolve().parents[1]
    return parse((root / "docs" / "reference" / "taxonomy.md").read_text(encoding="utf-8"))

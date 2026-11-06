import re
from collections import Counter

import pytest

from tools.taxonomy import load, parse


def test_real_taxonomy_matches_spec():
    t = load()
    assert t.vocab["ctype"] == (
        "feat", "fix", "docs", "chore", "refactor", "test", "ci", "build", "perf",
    )  # fmt: skip
    assert t.vocab["area"] == ("shell", "desktop", "host", "harness", "docs", "agents", "repo")
    names = [lab.name for lab in t.labels]
    assert len(names) == len(set(names)) == 20
    assert {"docs", "area:docs", "bug", "golden-update"} <= set(names)
    assert Counter(lab.dimension for lab in t.labels) == {
        "type": 4,
        "area": 7,
        "priority": 3,
        "state": 4,
        "switch": 2,
    }
    assert all(re.fullmatch(r"[0-9a-f]{6}", lab.colour) for lab in t.labels)
    assert all(0 < len(lab.description) <= 100 for lab in t.labels)
    assert [m for m, _ in t.milestones] == [
        "Backlog",
        "M1 Foundation",
        "M2 Principles",
        "M3 Home on NixOS",
    ]
    assert t.ctype_label["feat"] == "feature"
    assert t.ctype_label["fix"] == "bug"
    assert t.ctype_label["ci"] == "chore"
    assert t.area_label("shell") == "area:shell"


def test_parse_rejects_missing_section():
    with pytest.raises(ValueError, match="Labels"):
        parse("## Vocabulary\n\n| Name | Values |\n|---|---|\n| ctype | `feat` |\n")


def test_parse_rejects_duplicate_label():
    text = (
        "## Vocabulary\n\n| Name | Values |\n|---|---|\n| ctype | `feat` `fix` |\n\n"
        "## Labels\n\n| Label | Dimension | Colour | Description |\n|---|---|---|---|\n"
        "| `docs` | `type` | `a7b4bb` | Docs. |\n"
        "| `docs` | `type` | `a7b4bb` | Docs again. |\n\n"
        "## Commit types\n\n| ctype | Label |\n|---|---|\n| `feat` | `feature` |\n\n"
        "## Milestones\n\n| Milestone | Done when |\n|---|---|\n| Backlog | Default |\n"
    )
    with pytest.raises(ValueError, match="docs"):
        parse(text)

"""Repo agent-setup checks: CLAUDE.md link, AGENTS.md size, subagent models, skills."""

import re
import sys
from collections.abc import Sequence
from pathlib import Path

MODELS = {
    "implementer": "claude-sonnet-5-5",
    "checker": "claude-haiku-5-5",
    "reviewer": "claude-opus-5",
}
FORBIDDEN_MODELS = frozenset({"sonnet", "opus", "haiku", "fable", "inherit", "claude-opus-5-5"})
MAX_AGENTS_LINES = 199


def front_matter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t", "#")):
            out[key.strip()] = value.strip().strip("\"'")
    return None


def _own_skills(table_file: Path) -> set[str] | None:
    if not table_file.is_file():
        return None
    names: set[str] = set()
    inside = False
    for line in table_file.read_text().splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Own skills"
            continue
        if inside and line.lstrip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            found = re.findall(r"`([^`]+)`", cells[0]) if cells else []
            names.update(found)
    return names


def _check_agents(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((root / ".claude/agents").glob("*.md")):
        rel = f".claude/agents/{path.name}"
        stem = path.stem
        fm = front_matter(path.read_text())
        if stem not in MODELS:
            errors.append(f"{rel}: agent not listed in MODELS")
        if fm is None:
            errors.append(f"{rel}: missing front matter")
            continue
        if fm.get("name") != stem:
            errors.append(f"{rel}: front matter name must be {stem}")
        model = fm.get("model", "")
        if model in FORBIDDEN_MODELS:
            errors.append(f"{rel}: model {model!r} is forbidden; use an exact model ID")
        elif stem in MODELS and model != MODELS[stem]:
            errors.append(f"{rel}: model must be {MODELS[stem]}")
    return errors


def _check_skills(root: Path) -> list[str]:
    errors: list[str] = []
    skills_dir = root / ".claude/skills"
    dirs = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()
    listed = _own_skills(root / "docs/reference/skills.md")
    if listed is None:
        errors.append("docs/reference/skills.md: missing")
    else:
        for name in sorted(dirs - listed):
            errors.append(f".claude/skills/{name}: not in the Own skills table of skills.md")
        for name in sorted(listed - dirs):
            errors.append(f"docs/reference/skills.md: skill {name} has no .claude/skills folder")
    for name in sorted(dirs):
        skill = skills_dir / name / "SKILL.md"
        rel = f".claude/skills/{name}/SKILL.md"
        if not skill.is_file():
            errors.append(f"{rel}: missing")
            continue
        fm = front_matter(skill.read_text())
        if fm is None:
            errors.append(f"{rel}: missing front matter")
            continue
        if fm.get("name") != name:
            errors.append(f"{rel}: front matter name must be {name}")
        if not fm.get("description"):
            errors.append(f"{rel}: front matter description is missing")
    return errors


def check_repo(root: Path) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    claude = root / "CLAUDE.md"
    if not claude.is_symlink():
        errors.append("CLAUDE.md: must be a symlink to AGENTS.md")
    elif str(claude.readlink()) != "AGENTS.md":
        errors.append("CLAUDE.md: symlink target must be exactly AGENTS.md")
    agents = root / "AGENTS.md"
    if not agents.is_file():
        errors.append("AGENTS.md: missing")
    elif len(agents.read_text().splitlines()) > MAX_AGENTS_LINES:
        errors.append(f"AGENTS.md: more than {MAX_AGENTS_LINES} lines")
    errors += _check_agents(root)
    errors += _check_skills(root)
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    errors = check_repo(Path.cwd())
    for err in errors:
        print(err)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

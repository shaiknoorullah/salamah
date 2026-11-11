from pathlib import Path

from tools.agents.check import MODELS, check_repo


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _fixture(root: Path, model: str = MODELS["implementer"]) -> Path:
    _write(root / "AGENTS.md", "# Rules\n")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")
    _write(
        root / ".claude/agents/implementer.md",
        f"---\nname: implementer\ndescription: builds\nmodel: {model}\n---\nbody\n",
    )
    _write(
        root / ".claude/skills/new-issue/SKILL.md",
        "---\nname: new-issue\ndescription: file an issue\n---\nbody\n",
    )
    _write(
        root / "docs/reference/skills.md",
        "# Skills\n\n## Own skills\n\n| Skill | Job |\n|---|---|\n"
        "| `new-issue` | files issues |\n\n## External\n\n| Skill | Verdict |\n|---|---|\n"
        "| `other` | adopt |\n",
    )
    return root


def test_check_repo_clean_fixture(tmp_path):
    assert check_repo(_fixture(tmp_path)) == []


def test_check_repo_flags_alias_model(tmp_path):
    errors = check_repo(_fixture(tmp_path, model="sonnet"))
    assert any("implementer.md" in e and "model" in e for e in errors)


def test_check_repo_flags_missing_symlink(tmp_path):
    root = _fixture(tmp_path)
    (root / "CLAUDE.md").unlink()
    _write(root / "CLAUDE.md", "copy\n")
    errors = check_repo(root)
    assert any("CLAUDE.md" in e for e in errors)


def test_check_repo_flags_unlisted_skill(tmp_path):
    root = _fixture(tmp_path)
    _write(
        root / ".claude/skills/rogue/SKILL.md",
        "---\nname: rogue\ndescription: x\n---\n",
    )
    errors = check_repo(root)
    assert any("rogue" in e for e in errors)

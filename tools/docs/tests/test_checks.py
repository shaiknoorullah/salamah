from pathlib import Path

from tools.docs.checks import check_caps, check_front_matter, check_index, check_refs
from tools.docs.model import justfile_recipes, load_docs
from tools.taxonomy import Taxonomy

TAX = Taxonomy(
    {
        "doc-type": ("index", "guide", "reference", "decision"),
        "doc-status": ("slot", "draft", "current"),
        "decision-status": ("proposed", "accepted"),
    },
    (),
    (),
    {},
)
FM = "---\ntype: guide\nstatus: current\ncovers: []\nreviewed: 2026-11-05\n---\n"


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def doc(root: Path, rel: str):
    return next(d for d in load_docs(root) if d.path.as_posix() == rel)


def checks(problems):
    return [(p.line, p.check) for p in problems]


def test_front_matter_ok_and_missing(tmp_path):
    write(tmp_path, "docs/a.md", FM + "x\n")
    write(tmp_path, "docs/b.md", "no front matter\n")
    assert check_front_matter(doc(tmp_path, "docs/a.md"), TAX) == []
    (p,) = check_front_matter(doc(tmp_path, "docs/b.md"), TAX)
    assert (p.check, p.line, p.path) == ("front-matter", 1, "docs/b.md")


def test_bad_type_and_status(tmp_path):
    write(tmp_path, "docs/a.md", FM.replace("guide", "essay").replace("current", "x") + "y\n")
    msgs = [p.message for p in check_front_matter(doc(tmp_path, "docs/a.md"), TAX)]
    assert any("type" in m for m in msgs) and any("status" in m for m in msgs)


def test_missing_covers_and_bad_date(tmp_path):
    write(tmp_path, "docs/a.md", "---\ntype: guide\nstatus: draft\nreviewed: 2026-13-01\n---\n")
    msgs = [p.message for p in check_front_matter(doc(tmp_path, "docs/a.md"), TAX)]
    assert any("covers" in m for m in msgs) and any("reviewed" in m for m in msgs)


def test_decision_uses_decision_status(tmp_path):
    ok = FM.replace("guide", "decision").replace("current", "accepted")
    write(tmp_path, "docs/a.md", ok)
    write(tmp_path, "docs/b.md", ok.replace("accepted", "slot"))
    assert check_front_matter(doc(tmp_path, "docs/a.md"), TAX) == []
    assert len(check_front_matter(doc(tmp_path, "docs/b.md"), TAX)) == 1


def _tree(root: Path, root_links: str, folder_links: str) -> list:
    write(root, "docs/README.md", FM + root_links + "[x](guides/README.md)\n")
    write(root, "docs/guides/README.md", FM + folder_links + "[up](../README.md)\n")
    write(root, "docs/guides/a.md", FM + "[up](../README.md)\n")
    return load_docs(root)


def test_index_requires_both_links(tmp_path):
    assert check_index(_tree(tmp_path, "[a](./guides/../guides/a.md#top)\n", "[a](a.md)\n")) == []
    miss_root = check_index(_tree(tmp_path, "", "[a](a.md)\n"))
    assert [p.path for p in miss_root] == ["docs/guides/a.md"]
    miss_folder = check_index(_tree(tmp_path, "[a](guides/a.md)\n", ""))
    assert [p.path for p in miss_folder] == ["docs/guides/a.md"]


def test_folder_readme_only_needs_root_index(tmp_path):
    docs = _tree(tmp_path, "[a](guides/a.md)\n", "[a](a.md)\n")
    assert check_index(docs) == []
    write(tmp_path, "docs/README.md", FM + "[a](guides/a.md)\n")
    probs = check_index(load_docs(tmp_path))
    assert [p.path for p in probs] == ["docs/guides/README.md"]


def test_doc_without_link(tmp_path):
    docs = _tree(tmp_path, "[a](guides/a.md)\n", "[a](a.md)\n")
    write(tmp_path, "docs/guides/a.md", FM + "no links\n")
    probs = check_index(load_docs(tmp_path))
    assert [p.path for p in probs] == ["docs/guides/a.md"]
    assert docs


def _refs(root: Path, body: str):
    write(root, "docs/a.md", FM + body)
    return check_refs(doc(root, "docs/a.md"), root, justfile_recipes(root))


def test_refs_missing_path(tmp_path):
    write(tmp_path, "tools/x.py", "")
    probs = _refs(tmp_path, "ok `tools/x.py`\nbad `tools/y.py` and `flake.nix`\n")
    assert [(p.line, p.check) for p in probs] == [(8, "refs"), (8, "refs")]


def test_refs_glob_ok(tmp_path):
    write(tmp_path, "tools/x.py", "")
    assert _refs(tmp_path, "`tools/*.py`\n") == []
    assert len(_refs(tmp_path, "`tools/*.go`\n")) == 1


def test_refs_nested_glob(tmp_path):
    write(tmp_path, "tools/a/b/test_x.py", "")
    assert _refs(tmp_path, "`tools/**/test_*.py` `tools/*/test_x.py`\n") == []


def test_refs_unknown_recipe(tmp_path):
    write(tmp_path, "justfile", "x := 1\n# c:\ndocs:\n    echo\nfoo arg='a':\n    echo\n")
    assert _refs(tmp_path, "`just docs` `just foo` `just --list`\n") == []
    assert len(_refs(tmp_path, "`just nope`\n")) == 1


def test_refs_flake_attr(tmp_path):
    write(tmp_path, "flake.nix", "{ outputs = 1; }\n")
    write(tmp_path, "nix/checks.nix", "{ docs = 1; }\n")
    assert _refs(tmp_path, "`.#checks.x86_64-linux.docs`\n") == []
    assert len(_refs(tmp_path, "`.#checks.x86_64-linux.nothing`\n")) == 1


def test_refs_ignores_plain_text(tmp_path):
    body = "tools/none.py and just nope and .#zzz\n```\n`tools/none.py`\n```\n"
    assert _refs(tmp_path, body) == []


def _caps(root: Path, rel: str, text: str):
    write(root, rel, text)
    return check_caps(doc(root, rel))


def test_caps_151_lines_fails(tmp_path):
    assert _caps(tmp_path, "docs/a.md", FM + "x.\n" * (150 - 6)) == []
    (p,) = _caps(tmp_path, "docs/a.md", FM + "x.\n" * (151 - 6))
    assert (p.check, p.line) == ("caps", 151)


def test_reference_exempt(tmp_path):
    long = "x.\n" * 300
    assert _caps(tmp_path, "docs/a.md", FM.replace("guide", "reference") + long) == []
    assert _caps(tmp_path, "docs/b.md", FM.replace("current", "slot") + long) == []


def test_agents_200_fails_199_ok(tmp_path):
    assert _caps(tmp_path, "AGENTS.md", "x.\n" * 199) == []
    assert len(_caps(tmp_path, "AGENTS.md", "x.\n" * 200)) == 1


def test_readme_81_fails(tmp_path):
    assert _caps(tmp_path, "README.md", "x.\n" * 80) == []
    assert len(_caps(tmp_path, "README.md", "x.\n" * 81)) == 1


def test_sentence_26_words_fails(tmp_path):
    ok = " ".join(["w"] * 25) + ". " + "`a b c` " + " ".join(["w"] * 24) + "."
    assert _caps(tmp_path, "docs/a.md", FM + ok + "\n") == []
    bad = " ".join(["w"] * 26) + "."
    fence = "```\n" + bad + "\n```\n| " + bad + " |\n"
    (p,) = _caps(tmp_path, "docs/a.md", FM + fence + "\n" + bad + "\n")
    assert (p.check, p.line) == ("caps", 6 + 6)

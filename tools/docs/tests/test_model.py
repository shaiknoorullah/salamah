import pytest

from tools.docs.model import load_docs, parse_front_matter, prose_sentences


def test_front_matter_scalars_and_lists():
    text = "---\ntype: guide\ncovers: [a/*, b.md ]\nnone: []\n---\n# T\nbody\n"
    meta, body, start = parse_front_matter(text)
    assert meta == {"type": "guide", "covers": ["a/*", "b.md"], "none": []}
    assert body == "# T\nbody\n"
    assert start == 6


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("no front matter\n", 1),
        ("---\ntype guide\n---\n", 2),
        ("---\ntype: a\n\n---\n", 3),
        ("---\ntype: a\n", 3),
        ("---\ntype: a\ntype: b\n---\n", 3),
    ],
)
def test_front_matter_malformed_raises(text, line):
    with pytest.raises(ValueError, match=rf"^line {line}:"):
        parse_front_matter(text)


def test_front_matter_crlf_and_unicode(tmp_path):
    (tmp_path / "docs").mkdir()
    raw = "---\r\ntype: guide\r\ncovers: []\r\n---\r\nBismill\u0101h is said. See [x](y.md)"
    (tmp_path / "docs" / "a.md").write_bytes(raw.encode("utf-8"))
    (doc,) = load_docs(tmp_path)
    assert doc.meta["type"] == "guide"
    assert "Bismill\u0101h" in doc.body
    assert "\r" not in doc.body
    assert doc.body_start == 5
    assert doc.links == ("y.md",)
    assert doc.error is None


def test_load_docs_records_malformed_and_root_files(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "bad.md").write_text("---\noops\n---\nx\n")
    (tmp_path / "README.md").write_text("# Hi\n")
    docs = {str(d.path): d for d in load_docs(tmp_path)}
    assert docs["docs/bad.md"].error[0] == 2
    assert docs["README.md"].meta == {} and docs["README.md"].error is None


def test_links_skip_code():
    from tools.docs.model import extract_links

    body = "[a](x.md) `[b](no.md)`\n```\n[c](no2.md)\n```\n[d](z.md#f)\n"
    assert extract_links(body) == ("x.md", "z.md#f")


def test_prose_sentences_skips_non_prose():
    body = (
        "# Heading. Not prose.\n"
        "One two. Three `a.b c` four!\n"
        "```\nCode. Here.\n```\n"
        "| a | b. c |\n"
        "<!-- hidden. text\nmore -->\n"
        "- item five. Six\n"
    )
    assert list(prose_sentences(body)) == [
        (2, "One two."),
        (2, "Three X four!"),
        (9, "item five."),
        (9, "Six"),
    ]

"""Doc checks: front matter, index links, references and caps."""

import datetime
import fnmatch
import os
import posixpath
import re
from collections.abc import Sequence
from pathlib import Path

from tools.docs.model import Doc, Problem, prose_sentences, scan_lines
from tools.taxonomy import Taxonomy

ROOT_FILES = frozenset(
    "README.md AGENTS.md CLAUDE.md LICENSE SECURITY.md flake.nix flake.lock justfile Makefile"
    " .editorconfig .gitignore".split()
)
_PATH = re.compile(r"^(\.?[\w-]+/)+[\w.*-]+$")
_CODE = re.compile(r"`([^`]+)`")
_JUST = re.compile(r"^just\s+([A-Za-z_][\w-]*)")
MAX_WORDS = 25


def _p(doc: Doc, line: int, check: str, message: str) -> Problem:
    return Problem(doc.path.as_posix(), line, check, message)


def check_front_matter(doc: Doc, tax: Taxonomy) -> list[Problem]:
    if doc.error:
        return [_p(doc, doc.error[0], "front-matter", doc.error[1])]
    if doc.path.parts[0] != "docs":
        return []
    meta, out = doc.meta, []
    dtype = meta.get("type")
    if dtype not in tax.vocab["doc-type"]:
        out.append(_p(doc, 1, "front-matter", f"type {dtype!r} not in doc-type"))
    vocab = "decision-status" if dtype == "decision" else "doc-status"
    if meta.get("status") not in tax.vocab[vocab]:
        out.append(_p(doc, 1, "front-matter", f"status {meta.get('status')!r} not in {vocab}"))
    if not isinstance(meta.get("covers"), list):
        out.append(_p(doc, 1, "front-matter", "covers must be a list"))
    reviewed = meta.get("reviewed")
    try:
        if not isinstance(reviewed, str) or not re.fullmatch(r"\d{4}-\d\d-\d\d", reviewed):
            raise ValueError
        datetime.date.fromisoformat(reviewed)
    except ValueError:
        out.append(_p(doc, 1, "front-matter", "reviewed must be a YYYY-MM-DD date"))
    return out


def _resolved(doc: Doc) -> set[str]:
    out = set()
    for target in doc.links:
        target = target.split("#", 1)[0]
        if target and not re.match(r"^[A-Za-z][\w+.-]*:", target):
            out.add(posixpath.normpath(posixpath.join(doc.path.parent.as_posix(), target)))
    return out


def check_index(docs: Sequence[Doc]) -> list[Problem]:
    inside = [d for d in docs if d.path.parts[0] == "docs"]
    links = {d.path.as_posix(): _resolved(d) for d in inside}
    top = "docs/README.md"
    out = []
    for d in inside:
        me = d.path.as_posix()
        if not d.links:
            out.append(_p(d, 1, "index", "doc has no links"))
        if me == top:
            continue
        if d.path.name == "README.md":
            if me not in links.get(top, ()):
                out.append(_p(d, 1, "index", f"not linked from {top}"))
            continue
        readme = (d.path.parent / "README.md").as_posix()
        for index in dict.fromkeys((top, readme)):
            if index not in links:
                out.append(_p(d, 1, "index", f"{index} does not exist"))
            elif me not in links[index]:
                out.append(_p(d, 1, "index", f"not linked from {index}"))
    return out


def _repo_paths(root: Path) -> list[str]:
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel = Path(base).relative_to(root).as_posix()
        found += [posixpath.normpath(posixpath.join(rel, n)) for n in (*dirs, *files)]
    return found


def _nix_text(root: Path) -> str:
    files = [root / "flake.nix", *sorted((root / "nix").glob("**/*.nix"))]
    return "\n".join(f.read_text(encoding="utf-8") for f in files if f.is_file())


def check_refs(doc: Doc, root: Path, recipes: set[str]) -> list[Problem]:
    """Check backticked refs. `.#a.b.c` passes when the last component `c` is a whole word in
    flake.nix or nix/**/*.nix (output attrsets are built across those files)."""
    out, paths, nix = [], None, None
    for n, line in scan_lines(doc.body, doc.body_start):
        for tok in _CODE.findall(line):
            if m := _JUST.match(tok):
                if m.group(1) not in recipes:
                    out.append(_p(doc, n, "refs", f"unknown just recipe '{m.group(1)}'"))
            elif tok.startswith(".#"):
                nix = _nix_text(root) if nix is None else nix
                attr = tok[2:].split(".")[-1]
                if attr and not re.search(rf"(?<![\w-]){re.escape(attr)}(?![\w-])", nix):
                    out.append(_p(doc, n, "refs", f"flake attr '{tok}' not found in nix files"))
            elif _PATH.match(tok) or tok in ROOT_FILES:
                if "*" in tok:
                    paths = _repo_paths(root) if paths is None else paths
                    ok = any(fnmatch.fnmatchcase(p, tok) for p in paths)
                else:
                    ok = (root / tok).exists()
                if not ok:
                    out.append(_p(doc, n, "refs", f"path '{tok}' does not exist"))
    return out


def check_caps(doc: Doc) -> list[Problem]:
    out = []
    total = doc.body_start - 1 + len(doc.body.splitlines())
    name = doc.path.as_posix()
    exempt = doc.meta.get("type") == "reference" or doc.meta.get("status") == "slot"
    cap = {"README.md": 80, "AGENTS.md": 199}.get(name, None if exempt else 150)
    if cap and total > cap:
        out.append(_p(doc, cap + 1, "caps", f"{total} lines, cap is {cap}"))
    for line, sentence in prose_sentences(doc.body):
        words = len(sentence.split())
        if words > MAX_WORDS:
            out.append(_p(doc, doc.body_start - 1 + line, "caps", f"sentence has {words} words"))
    return out

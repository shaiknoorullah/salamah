"""Staleness: a doc is stale when a file it covers changed but the doc did not."""

import fnmatch
from collections.abc import Sequence

from tools.docs.model import Doc, Problem


def stale(changed: Sequence[str], docs: Sequence[Doc], no_doc_change: bool) -> list[Problem]:
    if no_doc_change:
        return []
    out = []
    for doc in docs:
        covers = doc.meta.get("covers")
        if doc.path.as_posix() in changed or not isinstance(covers, list):
            continue
        for file in changed:
            if any(fnmatch.fnmatchcase(file, glob) for glob in covers):
                out.append(Problem(doc.path.as_posix(), 1, "stale", f"covers {file}"))
    return out

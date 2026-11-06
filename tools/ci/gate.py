"""Fold the results of the CI jobs into one pass or fail."""

import json
import os
import sys
from collections.abc import Mapping, Sequence

_PASS = {"success", "skipped"}


def decide(needs: Mapping[str, Mapping[str, str]], soft: frozenset[str]) -> tuple[bool, list[str]]:
    ok, messages = True, []
    for job, info in sorted(needs.items()):
        result = info.get("result", "unknown")
        if result in _PASS:
            messages.append(f"ok: {job}: {result}")
        elif job in soft:
            messages.append(f"soft: {job}: {result} (does not block)")
        else:
            ok = False
            messages.append(f"FAIL: {job}: {result}")
    return ok, messages


def main(argv: Sequence[str] | None = None) -> int:
    raw = os.environ.get("NEEDS")
    if not raw:
        print("NEEDS is not set", file=sys.stderr)
        return 1
    soft = frozenset() if os.environ.get("E2E_SOFT") == "false" else frozenset({"e2e"})
    ok, messages = decide(json.loads(raw), soft)
    print("\n".join(messages))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

"""Sync repository labels and milestones from the taxonomy."""

import argparse
import sys
from collections.abc import Sequence

from tools import taxonomy
from tools.gh import rules
from tools.gh.api import GitHub


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.gh.sync")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune", action="store_true")
    args = parser.parse_args(argv)
    tax = taxonomy.load()
    gh = GitHub.from_env()
    labels = list(gh.paginate(f"/repos/{gh.repo}/labels"))
    miles = list(gh.paginate(f"/repos/{gh.repo}/milestones?state=all"))
    plan = rules.plan_labels(labels, tax.labels, args.prune)
    plan += rules.plan_milestones(miles, tax.milestones)
    for method, rel, body in plan:
        path = f"/repos/{gh.repo}/{rel}"
        print(f"{method} {path}")
        if not args.dry_run:
            gh.request(method, path, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())

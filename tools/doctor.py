"""Report missing tools and uninstalled git hooks. Always exits 0."""

import shutil
import subprocess
from collections.abc import Callable

TOOLS = ("nix", "just", "git", "python3", "gitleaks", "typos", "treefmt")


def problems(
    which: Callable[[str], str | None], git_config: Callable[[str], str | None]
) -> list[str]:
    found = [f"{tool} not found" for tool in TOOLS if which(tool) is None]
    if git_config("core.hooksPath") != ".githooks":
        found.append("git hooks not installed (run: just hooks)")
    return found


def _git_config(key: str) -> str | None:
    try:
        result = subprocess.run(["git", "config", key], capture_output=True, text=True, check=False)
    except OSError:
        return None
    value = result.stdout.strip()
    return value or None


def main() -> int:
    found = problems(shutil.which, _git_config)
    for problem in found:
        print(problem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

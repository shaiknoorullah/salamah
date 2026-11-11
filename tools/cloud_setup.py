"""Cloud session setup: install just, warm the nix dev shell. Never fails the session."""

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path


def plan(which: Callable[[str], str | None]) -> list[tuple[list[str], int]]:
    steps: list[tuple[list[str], int]] = []
    if not which("just"):
        steps.append((["uv", "tool", "install", "rust-just==1.59.0"], 120))
    steps.append(
        (
            [
                "nix",
                "build",
                "--no-link",
                "--extra-experimental-features",
                "nix-command flakes",
                ".#devShells.x86_64-linux.default",
            ],
            240,
        )  # fmt: skip
    )
    return steps


def _run(cmd: list[str], timeout: int) -> str:
    try:
        done = subprocess.run(cmd, timeout=timeout, capture_output=True, check=False)
        return f"exit {done.returncode}"
    except subprocess.TimeoutExpired:
        return f"timeout after {timeout}s"
    except Exception as exc:  # missing binary, permissions, anything else
        return f"error {type(exc).__name__}"


def main(argv: list[str] | None = None) -> int:
    try:
        log_dir = Path(os.path.expanduser("~")) / ".cache" / "salamah"
        log_dir.mkdir(parents=True, exist_ok=True)
        log = log_dir / "cloud-setup.log"
        for cmd, timeout in plan(shutil.which):
            start = time.monotonic()
            outcome = _run(cmd, timeout)
            took = time.monotonic() - start
            stamp = datetime.now(UTC).isoformat(timespec="seconds")
            line = f"{stamp} {' '.join(cmd)} -> {outcome} ({took:.1f}s)"
            with log.open("a") as fh:
                fh.write(line + "\n")
            print(f"cloud-setup: {outcome} ({took:.1f}s) {cmd[0]}")
    except Exception as exc:
        print(f"cloud-setup: skipped ({type(exc).__name__})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

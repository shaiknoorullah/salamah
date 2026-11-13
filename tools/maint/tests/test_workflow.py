"""The weekly-update job pushes through the pre-push hook, which needs a denylist (#29)."""

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[3] / ".github/workflows/scheduled.yml"


def _job(name: str) -> str:
    lines = WORKFLOW.read_text().splitlines()
    start = lines.index(f"  {name}:")
    is_job = re.compile(r"^  \S")
    end = next((i for i in range(start + 1, len(lines)) if is_job.match(lines[i])), len(lines))
    return "\n".join(lines[start:end])


def test_weekly_update_gives_hook_a_denylist():
    job = _job("weekly-update")
    assert "DENYLIST: ${{ secrets.DENYLIST }}" in job
    assert 'printf \'%s\\n\' "$DENYLIST" > "$RUNNER_TEMP/denylist"' in job
    assert "SALAMAH_DENYLIST: ${{ runner.temp }}/denylist" in job

import subprocess
from pathlib import Path

import pytest

from tools.ci import changes


def test_classify_desktop_paths():
    assert changes.classify(["shell/tests/x.qml"]) == {"desktop": True}
    assert changes.classify(["docs/README.md"]) == {"desktop": False}


def test_classify_flake_and_empty():
    assert changes.classify(["flake.lock"])["desktop"] is True
    assert changes.classify([])["desktop"] is False


def test_main_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    out = tmp_path / "out"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setattr(changes, "changed_files", lambda base: ["modules/a.nix"])
    assert changes.main(["--base", "origin/main"]) == 0
    assert out.read_text() == "desktop=true\n"


def test_main_prints_without_output_file(monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setattr(changes, "changed_files", lambda base: ["docs/a.md"])
    assert changes.main(["--base", "origin/main"]) == 0
    assert capsys.readouterr().out == "desktop=false\n"


def test_changed_files_falls_back_to_two_dot(monkeypatch: pytest.MonkeyPatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd[-1])
        code = 128 if cmd[-1].endswith("...HEAD") else 0
        return subprocess.CompletedProcess(cmd, code, stdout="a\nb\n", stderr="")

    monkeypatch.setattr(changes.subprocess, "run", fake_run)
    assert changes.changed_files("origin/main") == ["a", "b"]
    assert calls == ["origin/main...HEAD", "origin/main..HEAD"]

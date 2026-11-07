import pytest

from tools.ci import gate

SOFT = frozenset({"e2e"})


def _needs(**results: str) -> dict[str, dict[str, str]]:
    return {k: {"result": v} for k, v in results.items()}


def test_decide_skipped_passes():
    ok, _ = gate.decide(_needs(fast="success", **{"pr-rules": "skipped"}), SOFT)
    assert ok


def test_decide_failure_fails():
    ok, msgs = gate.decide(_needs(fast="failure", eval="success"), SOFT)
    assert not ok
    assert any("fast" in m and "failure" in m for m in msgs)


def test_decide_soft_e2e_passes():
    assert gate.decide(_needs(e2e="failure"), SOFT)[0]
    assert not gate.decide(_needs(e2e="failure"), frozenset())[0]


def test_decide_cancelled_fails():
    assert not gate.decide(_needs(eval="cancelled"), SOFT)[0]


def test_main_reads_env(monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.setenv("NEEDS", '{"fast": {"result": "success"}, "e2e": {"result": "failure"}}')
    monkeypatch.delenv("E2E_SOFT", raising=False)
    assert gate.main([]) == 0
    assert "fast" in capsys.readouterr().out
    monkeypatch.setenv("E2E_SOFT", "false")
    assert gate.main([]) == 1


def test_main_missing_needs(monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.delenv("NEEDS", raising=False)
    assert gate.main([]) == 1
    assert "NEEDS" in capsys.readouterr().err

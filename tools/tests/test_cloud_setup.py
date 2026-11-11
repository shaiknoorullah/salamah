from tools import cloud_setup


def test_plan_installs_just_only_when_missing():
    missing = cloud_setup.plan(lambda t: None)
    present = cloud_setup.plan(lambda t: "/bin/" + t)
    assert (["uv", "tool", "install", "rust-just==1.59.0"], 120) in missing
    assert all(cmd[:2] != ["uv", "tool"] for cmd, _ in present)
    nix = (
        [
            "nix", "build", "--no-link", "--extra-experimental-features",
            "nix-command flakes", ".#devShells.x86_64-linux.default",
        ],
        240,
    )  # fmt: skip
    assert missing[-1] == nix
    assert present == [nix]


def test_main_always_exits_0(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        cloud_setup,
        "plan",
        lambda which: [
            (["definitely-not-a-binary-xyz"], 5),
            (["sh", "-c", "exit 3"], 5),
        ],
    )
    assert cloud_setup.main([]) == 0
    log = (tmp_path / ".cache/salamah/cloud-setup.log").read_text()
    assert "definitely-not-a-binary-xyz" in log
    assert "exit 3" in log
    assert capsys.readouterr().out

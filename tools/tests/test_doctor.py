from tools.doctor import problems


def test_doctor_reports_missing_tools_and_hooks():
    probs = problems(
        which=lambda t: None if t == "just" else "/bin/" + t, git_config=lambda k: None
    )
    assert "just not found" in probs
    assert "git hooks not installed (run: just hooks)" in probs
    assert problems(which=lambda t: "/bin/" + t, git_config=lambda k: ".githooks") == []

from tools import taxonomy
from tools.gh import rules

TAX = taxonomy.load()
GOOD = "someone" + "@" + "corp-mail.test"
OK = "noreply@github.com"


def test_issue_ref_closes_and_part_of():
    assert rules.find_issue_ref("## What\nx\n## Issue\nCloses #12\n") == ("Closes", 12)
    assert rules.find_issue_ref("## Issue\n\nPart of #3\n## Try it\nCloses #9") == ("Part of", 3)


def test_issue_ref_ignores_code_and_comments():
    fence = "## Issue\n```\nCloses #9\n```\n~~~\nCloses #9\n~~~\n"
    assert rules.find_issue_ref(fence) is None
    assert rules.find_issue_ref("## Issue\n<!--\nCloses #9\n-->\n") is None
    assert rules.find_issue_ref("## Issue\n<!-- Closes #9 -->\nCloses #4") == ("Closes", 4)


def test_issue_ref_needs_issue_section():
    assert rules.find_issue_ref("## What\nCloses #9\n") is None
    assert rules.find_issue_ref("## Issue\n## Links\nCloses #9\n") is None


def test_title_rules():
    assert rules.check_title("feat(repo): GitHub automation", TAX) == []
    assert rules.check_title("feat(repo): x (#5)", TAX)
    assert rules.check_title("feature(repo): x", TAX)
    assert rules.check_title("feat(repo): " + "x" * 70, TAX)


def test_branch_rules():
    assert rules.check_branch("feat/12-hello", 12, TAX) == []
    assert rules.check_branch("feat/12-hello", 13, TAX)
    assert rules.check_branch("feature/12-x", 12, TAX)
    assert rules.check_branch("feat/12-Hello", 12, TAX)


def commit(sha, subject, a=OK, c=OK, parents=1):
    return {
        "sha": sha,
        "parents": [{}] * parents,
        "commit": {
            "message": subject + "\n\nbody",
            "author": {"email": a},
            "committer": {"email": c},
        },
    }


def test_commits_skip_merges_and_check_emails():
    commits = [
        commit("a1" * 20, "feat(repo): ok (#5)"),
        commit("b2" * 20, "Merge main", parents=2),
        commit("c3" * 20, "feat(repo): wrong (#6)"),
        commit("d4" * 20, "feat(repo): mail (#5)", a=GOOD),
        commit("e5" * 20, "feat(repo): mail (#5)", c=GOOD),
    ]
    errs = rules.check_commits(commits, 5, TAX)
    assert len(errs) == 3
    assert not any(GOOD in e for e in errs)
    assert any("c3c3c3c" in e for e in errs)
    assert rules.check_commits(commits[:2], 5, TAX) == []


def issue(**kw):
    base = {
        "state": "open",
        "labels": [{"name": "feature"}, {"name": "area:repo"}],
        "milestone": {"title": "M1 Foundation"},
    }
    return {**base, **kw}


def test_issue_rules():
    assert rules.check_issue(issue(), TAX) == []
    assert len(rules.check_issue(issue(state="closed"), TAX)) == 1
    assert len(rules.check_issue(issue(labels=[{"name": "feature"}]), TAX)) == 1
    two = [{"name": "feature"}, {"name": "bug"}, {"name": "area:repo"}]
    assert len(rules.check_issue(issue(labels=two), TAX)) == 1
    assert len(rules.check_issue(issue(milestone=None), TAX)) == 1


def test_goldens_need_label():
    assert rules.check_goldens(["tests/golden/a.png"], [])
    assert rules.check_goldens(["tests/golden/a.png"], ["golden-update"]) == []
    assert rules.check_goldens(["src/a.png"], []) == []


def test_form_labels():
    body = "### Type\n\nfeature\n\n### Area\n\nshell, docs"
    assert rules.form_labels(body, TAX) == ["feature", "area:shell", "area:docs"]
    body = "### type\n\n_No response_\n\n### AREA\n\nnope, repo, repo\n\n### Other\n\nbug"
    assert rules.form_labels(body, TAX) == ["area:repo"]
    assert rules.form_labels("### Type\n\nbogus, bug", TAX) == ["bug"]


def test_issue_ref_ignores_unclosed_fence_comment_and_inline_code():
    assert rules.find_issue_ref("## Issue\n\n```text\nCloses #9\n") is None
    assert rules.find_issue_ref("## Issue\n\n<!-- Closes #9\n") is None
    assert rules.find_issue_ref("## Issue\n\n`Closes #9`\n") is None
    assert rules.find_issue_ref("## Issue\n\n  ~~~~\nCloses #9\n  ~~~~\n\nPart of #4\n") == (
        "Part of",
        4,
    )

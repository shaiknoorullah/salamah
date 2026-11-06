from tools import taxonomy
from tools.gh import rules, sync
from tools.taxonomy import Label

L = [Label("bug", "type", "ff0000", "Broken."), Label("area:shell", "area", "c5d1d8", "Shell.")]


def test_plan_labels_create_patch_prune():
    existing = [
        {"name": "bug", "color": "FF0000", "description": "Broken."},
        {"name": "area:shell", "color": "000000", "description": "Shell."},
        {"name": "old", "color": "111111", "description": ""},
    ]
    assert rules.plan_labels(existing, L, False) == [
        ("PATCH", "labels/area%3Ashell", {"color": "c5d1d8", "description": "Shell."}),
    ]
    plan = rules.plan_labels(existing[:1] + existing[2:], L, True)
    assert plan[0] == (
        "POST",
        "labels",
        {"name": "area:shell", "color": "c5d1d8", "description": "Shell."},
    )
    assert plan[1] == ("DELETE", "labels/old", None)
    assert rules.plan_labels([], L[:1], False)[0][0] == "POST"


def test_plan_milestones():
    existing = [
        {"number": 7, "title": "A", "description": "old"},
        {"number": 8, "title": "B", "description": "b"},
    ]
    wanted = [("A", "new"), ("B", "b"), ("C", "c")]
    assert rules.plan_milestones(existing, wanted) == [
        ("PATCH", "milestones/7", {"description": "new"}),
        ("POST", "milestones", {"title": "C", "state": "open", "description": "c"}),
    ]


class Fake:
    repo = "o/r"

    def __init__(self):
        self.calls = []

    def paginate(self, path):
        self.calls.append(("PAGE", path))
        return iter([])

    def request(self, method, path, body=None, **kw):
        self.calls.append((method, path, body))


def test_main_dry_run_and_apply(monkeypatch, capsys):
    fake = Fake()
    monkeypatch.setattr(sync.GitHub, "from_env", classmethod(lambda cls: fake))
    tax = taxonomy.load()
    assert sync.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert out.count("POST /repos/o/r/labels") == len(tax.labels)
    assert out.count("POST /repos/o/r/milestones") == len(tax.milestones)
    assert not [c for c in fake.calls if c[0] == "POST"]
    assert sync.main([]) == 0
    assert len([c for c in fake.calls if c[0] == "POST"]) == len(tax.labels) + len(tax.milestones)

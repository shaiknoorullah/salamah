import email.message
import io
import json
import urllib.error

import pytest

from tools.gh.api import GitHub, GitHubError


class Resp:
    def __init__(self, body: bytes, ctype: str = "application/json", link: str | None = None):
        self._body = body
        self.headers = email.message.Message()
        self.headers["Content-Type"] = ctype
        if link:
            self.headers["Link"] = link

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def make(responses):
    calls = []

    def fake(req):
        calls.append(req)
        r = responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    return GitHub("o/r", "tok123", urlopen=fake), calls


def test_request_headers_and_json():
    gh, calls = make(
        [Resp(b'{"a": 1}'), Resp(b"", "application/json"), Resp(b"diff", "text/plain")]
    )
    assert gh.request("POST", "/repos/o/r/issues", {"t": 1}) == {"a": 1}
    req = calls[0]
    assert req.full_url == "https://api.github.com/repos/o/r/issues"
    assert req.get_method() == "POST"
    assert json.loads(req.data) == {"t": 1}
    h = {k.lower(): v for k, v in req.header_items()}
    assert h["authorization"] == "Bearer tok123"
    assert h["x-github-api-version"] == "2022-11-28"
    assert h["accept"] == "application/vnd.github+json"
    assert h["content-type"] == "application/json"
    assert gh.request("DELETE", "/x") is None
    assert calls[1].data is None
    assert gh.request("GET", "/x", accept="application/vnd.github.diff") == "diff"


def test_paginate_follows_link():
    nxt = '<https://api.github.com/page2>; rel="next", <https://api.github.com/p9>; rel="last"'
    gh, calls = make([Resp(b'[{"n":1}]', link=nxt), Resp(b'[{"n":2}]')])
    assert list(gh.paginate("/things")) == [{"n": 1}, {"n": 2}]
    assert calls[1].full_url == "https://api.github.com/page2"


def test_error_status():
    err = urllib.error.HTTPError("u", 404, "Not Found", email.message.Message(), io.BytesIO(b"{}"))
    gh, _ = make([err])
    with pytest.raises(GitHubError) as e:
        gh.request("GET", "/x")
    assert e.value.status == 404
    assert "tok123" not in str(e.value)


def test_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert GitHub.from_env().repo == "o/r"
    monkeypatch.delenv("GITHUB_TOKEN")
    with pytest.raises(GitHubError):
        GitHub.from_env()


def test_request_bytes_returns_raw():
    gh, calls = make([Resp(b"\x89PNG\x00\xff", "application/octet-stream")])
    assert gh.request_bytes("/repos/o/r/contents/a.png?ref=x") == b"\x89PNG\x00\xff"
    assert calls[0].get_header("Accept") == "application/vnd.github.raw"

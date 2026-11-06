"""Minimal GitHub REST client on urllib (stdlib only)."""

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from typing import Any

_NEXT = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


class GitHubError(Exception):
    def __init__(self, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.status = status


class GitHub:
    def __init__(
        self,
        repo: str,
        token: str,
        *,
        base: str = "https://api.github.com",
        urlopen: Callable = urllib.request.urlopen,
    ) -> None:
        self.repo, self._token, self._base, self._urlopen = repo, token, base, urlopen

    @classmethod
    def from_env(cls) -> "GitHub":
        repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
        if not repo or not token:
            raise GitHubError("GITHUB_REPOSITORY and GITHUB_TOKEN must be set")
        return cls(repo, token)

    def _send(self, method: str, url: str, body: Mapping | None, accept: str) -> Any:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": accept,
            "User-Agent": "salamah-tools",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with self._urlopen(req) as resp:
                raw = resp.read()
                return resp, raw
        except urllib.error.HTTPError as e:
            raise GitHubError(
                f"{method} {url.removeprefix(self._base)}: HTTP {e.code}", e.code
            ) from e

    @staticmethod
    def _decode(resp: Any, raw: bytes) -> Any:
        if "json" in (resp.headers.get("Content-Type") or "").lower():
            return json.loads(raw) if raw.strip() else None
        return raw.decode("utf-8", errors="replace")

    def request(
        self,
        method: str,
        path: str,
        body: Mapping | None = None,
        *,
        accept: str = "application/vnd.github+json",
    ) -> Any:
        return self._decode(*self._send(method, self._base + path, body, accept))

    def paginate(self, path: str) -> Iterator[dict]:
        url: str | None = self._base + path
        while url:
            resp, raw = self._send("GET", url, None, "application/vnd.github+json")
            yield from self._decode(resp, raw) or []
            m = _NEXT.search(resp.headers.get("Link") or "")
            url = m.group(1) if m else None

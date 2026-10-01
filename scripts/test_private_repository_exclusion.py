#!/usr/bin/env python3
from __future__ import annotations

from sync_repository import sync_repository


class PrivateRepositoryGitHub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def repo(self, repository: str) -> dict:
        self.calls.append(("repo", repository))
        return {
            "id": 999999999,
            "full_name": repository,
            "default_branch": "main",
            "private": True,
        }

    def __getattr__(self, name: str):
        raise AssertionError(
            f"private repository exclusion failed before unexpected GitHub call: {name}"
        )


gh = PrivateRepositoryGitHub()
repository = "HereLiesAz/private-fixture"

try:
    sync_repository(gh, repository, worker_url="", dry_run=True)
except RuntimeError as exc:
    message = str(exc)
    assert "private repositories are excluded from central sync" in message, message
else:
    raise AssertionError("private repository was accepted by central sync")

assert gh.calls == [("repo", repository)], gh.calls
print("private repository exclusion regression test passed")

#!/usr/bin/env python3
"""A push that changes a repository's workflow setup requests a sync of that repository."""
from __future__ import annotations

from dispatch_request import _request_sync_if_setup_changed


class FakeGitHub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def json(self, method: str, path: str, body=None):
        self.calls.append((method, path, body))
        return None


def run(ref: str, changed: list[str] | None):
    gh = FakeGitHub()
    result = _request_sync_if_setup_changed(gh, "HereLiesAz/example", "main", {"ref": ref}, changed)
    return result, gh.calls


# Workflow files or the request menu changed on the default branch: sync that repository.
for path in (".github/workflows/deploy.yml", ".github/workflow-request.yml"):
    result, calls = run("refs/heads/main", ["src/app.js", path])
    assert result and result["changed"] == [path], result
    assert calls == [(
        "POST",
        "/repos/HereLiesAz/workflows/actions/workflows/sync-repository.yml/dispatches",
        {"ref": "main", "inputs": {"repository": "HereLiesAz/example"}},
    )], calls

# Other branches, other files, or unknown file lists never request a sync.
for ref, changed in (
    ("refs/heads/feature", [".github/workflows/deploy.yml"]),
    ("refs/heads/main", ["src/app.js", ".github/ISSUE_TEMPLATE/bug.yml"]),
    ("refs/heads/main", None),
    ("refs/tags/v1", [".github/workflows/deploy.yml"]),
):
    result, calls = run(ref, changed)
    assert result is None and calls == [], (ref, changed)

print("sync-on-setup-change regression test passed")

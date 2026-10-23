#!/usr/bin/env python3
"""Regression test: pull-request heads outside the target repository never reach secrets."""
from __future__ import annotations

from dispatch_request import _untrusted_pull_request_head

REPO = "HereLiesAz/hereliesaz.github.io"


def pr(head_repo):
    return {"pull_request": {"head": {"repo": head_repo}}}


# Same-repository branch: trusted (case-insensitive owner/name).
assert not _untrusted_pull_request_head(pr({"full_name": REPO, "fork": False}), REPO)
assert not _untrusted_pull_request_head(pr({"full_name": REPO.upper(), "fork": False}), REPO)
# Fork flag set.
assert _untrusted_pull_request_head(pr({"full_name": "someone/hereliesaz.github.io", "fork": True}), REPO)
# Deleted fork: GitHub nulls head.repo. Must fail closed.
assert _untrusted_pull_request_head(pr(None), REPO)
assert _untrusted_pull_request_head({"pull_request": {"head": {}}}, REPO)
assert _untrusted_pull_request_head({"pull_request": {}}, REPO)
assert _untrusted_pull_request_head({}, REPO)
# A different, non-fork repository is still untrusted.
assert _untrusted_pull_request_head(pr({"full_name": "someone/else", "fork": False}), REPO)
print("dispatch request guard ok")

#!/usr/bin/env python3
"""Regression test: a huge push event is shrunk below GitHub's workflow_dispatch input cap."""
from __future__ import annotations

import json

from dispatch_request import MAX_DISPATCH_EVENT_JSON, _event_json_for_dispatch

small = {"ref": "refs/heads/main", "commits": [{"id": "a", "message": "m", "added": ["x"]}]}
assert json.loads(_event_json_for_dispatch(small)) == small

big = {
    "ref": "refs/heads/main",
    "head_commit": {"id": "h", "message": "merge"},
    "commits": [
        {"id": str(i), "message": "c" * 200, "added": [f"f{j}" for j in range(40)], "modified": ["m"] * 40}
        for i in range(400)
    ],
}
text = _event_json_for_dispatch(big)
assert len(text) <= MAX_DISPATCH_EVENT_JSON, len(text)
out = json.loads(text)
assert out["head_commit"] == big["head_commit"] and out["ref"] == big["ref"]
assert all("added" not in c for c in out["commits"])
print("dispatch event size ok")

#!/usr/bin/env python3
"""Regression test: a huge push event is shrunk below GitHub's workflow_dispatch input cap."""
from __future__ import annotations

import json

from dispatch_request import MAX_DISPATCH_EVENT_JSON, MAX_DISPATCH_INPUTS_JSON, _event_json_for_dispatch, _fit_dispatch_inputs

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

# head_commit file lists and a bloated repository object shrink when commits alone are not enough.
fat = {
    "ref": "refs/heads/main",
    "commits": [],
    "head_commit": {"id": "h", "message": "m", "added": [f"file{i}.kt" for i in range(5000)]},
    "repository": {"id": 1, "full_name": "o/r", "description": "d" * 50_000, "owner": {"id": 2, "login": "o", "x": "y"}},
}
out = json.loads(_event_json_for_dispatch(fat))
assert "added" not in out["head_commit"] and out["repository"] == {"id": 1, "full_name": "o/r", "owner": {"id": 2, "login": "o"}}

# The whole inputs object fits GitHub's total cap, even when other inputs are large.
inputs = {
    "target_repository": "o/r",
    "target_vars_json": json.dumps({"V": "v" * 25_000}),
    "target_event_json": json.dumps(big, separators=(",", ":")),
}
fitted = _fit_dispatch_inputs(inputs, big)
assert len(json.dumps(fitted, separators=(",", ":"))) <= MAX_DISPATCH_INPUTS_JSON
assert json.loads(fitted["target_event_json"])["head_commit"] == big["head_commit"]
assert fitted["target_vars_json"] == inputs["target_vars_json"]
print("dispatch event size ok")

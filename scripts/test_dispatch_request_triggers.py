#!/usr/bin/env python3
"""Regression test: which pushed refs, paths and PR activities start a registered workflow.

Uses the real registered Theater Bake source, so a change to its `on:` block
(for example dropping the default-branch filter) fails here.
"""
from __future__ import annotations

import json
from pathlib import Path

from dispatch_request import _event_trigger
from sync_repository_catalog import load_yaml

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "registry/1148736516/manifest.json").read_text(encoding="utf-8"))
bake = manifest["workflows"][".github/workflows/theater_bake.yml"]
source = load_yaml((ROOT / bake["registry_source"]).read_text(encoding="utf-8"))

CROPS = ["scripts/crops.json"]
TRACKER = [".github/workflows/theater_bake.yml"]


def push(ref, files):
    return _event_trigger(source, "push", {"ref": ref}, files)


# The bake runs the pushed branch's own scripts with HF_TOKEN and the publish PAT, so only
# the default branch may trigger it by push.
assert push("refs/heads/main", CROPS) == "push"
assert push("refs/heads/main", TRACKER) == "push"
assert push("refs/heads/ccr-4aa0607d-kjzqdl", CROPS) is None
assert push("refs/heads/feat/anything", TRACKER) is None
assert push("refs/heads/main-but-not-main", CROPS) is None
assert push("refs/tags/main", CROPS) is None                      # a tag named like the branch
# Paths still matter on main.
assert push("refs/heads/main", ["src/App.jsx"]) is None
assert push("refs/heads/main", ["src/App.jsx", "scripts/crops.json"]) == "push"
# Manual dispatch is unaffected by branch or paths.
assert _event_trigger(source, "workflow_dispatch", {}, None) == "workflow_dispatch"
# Events the source does not declare never match.
assert _event_trigger(source, "pull_request", {"action": "opened"}, CROPS) is None
assert _event_trigger(source, "issues", {"action": "opened"}, None) is None

# Generic semantics the filter above relies on, on a throwaway document.
doc = {"on": {"pull_request": {"branches": ["main"]}, "push": {"branches-ignore": ["wip/**"], "tags": ["v*"]}}}
pr = lambda action, base: _event_trigger(doc, "pull_request", {"action": action, "pull_request": {"base": {"ref": base}}}, None)
assert pr("opened", "main") == "pull_request"
assert pr("synchronize", "main") == "pull_request"
assert pr("labeled", "main") is None                              # not in GitHub's default activity set
assert pr("opened", "release") is None                            # base branch filter
assert _event_trigger(doc, "push", {"ref": "refs/heads/wip/x"}, None) is None   # branches-ignore
assert _event_trigger(doc, "push", {"ref": "refs/tags/v1"}, None) == "push"
assert _event_trigger(doc, "push", {"ref": "refs/tags/x1"}, None) is None
assert _event_trigger(doc, "push", {"ref": "refs/heads/main"}, None) is None     # tags-only: a branch push never starts it
assert _event_trigger({"on": {"push": {"branches": ["main"]}}}, "push", {"ref": "refs/tags/v1"}, None) is None  # branches-only: a tag never does
assert _event_trigger({"on": ["push"]}, "push", {"ref": "refs/heads/anything"}, None) == "push"
assert _event_trigger({"on": "workflow_dispatch"}, "push", {}, None) is None
ignore = {"on": {"push": {"paths-ignore": ["docs/**"]}}}
assert _event_trigger(ignore, "push", {"ref": "refs/heads/main"}, ["docs/a.md"]) is None
assert _event_trigger(ignore, "push", {"ref": "refs/heads/main"}, ["docs/a.md", "src/a.py"]) == "push"

print("dispatch trigger matching ok")

#!/usr/bin/env python3
"""The Worker's event-consumer map is current and never drops an event the gateway would route."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from dispatch_request import _event_trigger
from generate_event_consumers import (
    MODULE_PATH,
    NON_WEBHOOK_TRIGGERS,
    ROOT,
    build_consumer_map,
    parse_module,
    render_module,
    repository_events,
    trigger_names,
)
from ruamel.yaml import YAML

# 1. The committed module is exactly what the registry generates.
consumers = build_consumer_map()
committed = (ROOT / MODULE_PATH).read_text(encoding="utf-8")
assert committed == render_module(consumers), (
    f"{MODULE_PATH} is stale; run python scripts/generate_event_consumers.py"
)
assert parse_module(committed) == consumers

# 2. No gap against the real routing function. For every active registered workflow, strip all
#    branch/path/action filters (the most permissive form of its trigger) and ask
#    dispatch_request._event_trigger which webhook events it accepts. Each must be forwarded.
universe = {
    "push", "pull_request", "pull_request_target", "pull_request_review",
    "pull_request_review_comment", "issues", "issue_comment", "label", "create", "delete",
    "release", "workflow_run", "repository_dispatch", "discussion", "discussion_comment",
    "merge_group", "milestone", "page_build", "public", "registry_package", "status",
    "check_run", "check_suite", "deployment", "deployment_status", "fork", "gollum",
    "project", "watch", "branch_protection_rule", "workflow_dispatch", "schedule",
}
for source in (ROOT / "registry").glob("*/*.source.yml"):
    try:
        universe.update(trigger_names(source.read_text(encoding="utf-8")))
    except Exception:
        pass

universe -= NON_WEBHOOK_TRIGGERS  # never delivered as webhooks, so never reach the Worker
checked = 0
for manifest_file in sorted((ROOT / "registry").glob("*/manifest.json")):
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    repository_id = str((manifest.get("repository") or {}).get("id") or "")
    if not repository_id:
        continue
    forwarded = set(consumers[repository_id]["events"])
    assert "push" in forwarded, repository_id  # setup-change re-sync needs every push
    for source_path, entry in (manifest.get("workflows") or {}).items():
        if not isinstance(entry, dict) or entry.get("status") != "active":
            continue
        doc = YAML(typ="safe").load((ROOT / entry["registry_source"]).read_text(encoding="utf-8")) or {}
        stripped = copy.deepcopy(doc)
        if isinstance(stripped.get("on"), dict):
            stripped["on"] = {key: None for key in stripped["on"]}
        for event_name in universe:
            if _event_trigger(stripped, event_name, {}, None):
                assert event_name in forwarded, (manifest_file, source_path, event_name)
                checked += 1
assert checked > 0

# 3. Trigger naming rules on synthetic manifests.
sources = {
    "a.yml": "on:\n  pull_request_target:\n    types: [opened]\n",
    "b.yml": "on:\n  push:\n    branches: [release/*]\n  schedule:\n    - cron: '0 0 * * *'\n",
    "c.yml": "on: [issues, issue_comment, label]\n",
    "d.yml": "on: create\n",
    "e.yml": "on:\n  delete:\n  workflow_call:\n",
    "f.yml": "on:\n  workflow_run:\n    workflows: [CI]\n",
}
manifest = {"workflows": {
    "a": {"status": "active", "registry_source": "a.yml"},
    "b": {"status": "active", "registry_source": "b.yml"},
    "c": {"status": "active", "registry_source": "c.yml"},
    "d": {"status": "active", "registry_source": "d.yml"},
    "e": {"status": "active", "registry_source": "e.yml"},
    "f": {"status": "local", "registry_source": "f.yml"},
}}
events = repository_events(manifest, sources.__getitem__)
assert events == ["create", "delete", "issue_comment", "issues", "label", "pull_request", "push"], events
assert repository_events({"workflows": {}}, sources.__getitem__) == ["push"]

# 4. A repository sync replaces only its own row, and retries on a concurrent-write conflict.
import sync_repository
from sync_repository_catalog import ApiError


class FakeGitHub:
    def __init__(self, files: dict[str, str], conflicts: int = 0) -> None:
        self.files = dict(files)
        self.conflicts = conflicts
        self.puts = 0

    def get_file(self, full_name, path, ref=None):
        if path not in self.files:
            raise ApiError(f"GET {path} -> 404: missing")
        return self.files[path], "sha"

    def put_file(self, full_name, path, content, message, branch=None):
        self.puts += 1
        if self.conflicts:
            self.conflicts -= 1
            self.files[path] = render_module({**parse_module(self.files[path]), "77": {"repository": "HereLiesAz/other", "events": ["push"]}})
            raise ApiError(f"PUT {path} -> 409: conflict")
        self.files[path] = content


sync_repository.time.sleep = lambda _seconds: None
fake_manifest = {
    "repository": {"id": 42, "full_name": "HereLiesAz/fixture"},
    "workflows": {".github/workflows/ci.yml": {"status": "active", "registry_source": "registry/42/ci.source.yml"}},
}
fake = FakeGitHub({
    "registry/42/manifest.json": json.dumps(fake_manifest),
    "registry/42/ci.source.yml": "on:\n  pull_request_target:\n  push:\n    branches: [main]\n",
    MODULE_PATH: render_module({"42": {"repository": "HereLiesAz/fixture", "events": ["push"]}, "7": {"repository": "HereLiesAz/seven", "events": ["push", "issues"]}}),
}, conflicts=1)
outcome = sync_repository._refresh_event_consumers(fake, 42)
after = parse_module(fake.files[MODULE_PATH])
assert outcome == {"changed": True, "events": ["pull_request", "push"]}, outcome
assert after["42"]["events"] == ["pull_request", "push"], after
assert after["7"]["events"] == ["push", "issues"] and "77" in after, after
assert fake.puts == 2
assert sync_repository._refresh_event_consumers(fake, 42)["changed"] is False and fake.puts == 2

print(f"event-consumer map test passed ({len(consumers)} repositories, {checked} routed pairs checked)")

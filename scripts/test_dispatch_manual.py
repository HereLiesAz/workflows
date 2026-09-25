#!/usr/bin/env python3
"""Regression test for dispatch_manual's workflow matching and catch-up selection."""
from __future__ import annotations

from pathlib import Path

from dispatch_manual import _push_on_default_branch, _resolve_workflows
from sync_repository_catalog import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def doc(text: str) -> dict:
    return load_yaml(text)


# Catch-up runs only workflows that fire on pushes to the default branch.
assert _push_on_default_branch(doc("on:\n  push:\n    branches: [main]\n"), "main")
assert _push_on_default_branch(doc("on: [push, pull_request]\n"), "main")
assert _push_on_default_branch(doc("on:\n  push:\n    branches: ['releases/**', 'ma*']\n"), "main")
assert not _push_on_default_branch(doc("on:\n  push:\n    branches: [develop]\n"), "main")
assert not _push_on_default_branch(doc("on:\n  push:\n    tags: ['v*']\n"), "main")
assert not _push_on_default_branch(doc("on:\n  pull_request:\n  workflow_dispatch:\n"), "main")

# A real registered source: stremio-soundtrack's deploy workflow.
for source in ROOT.glob("registry/*/deploy-*.source.yml"):
    if "wrangler-action" in source.read_text(encoding="utf-8"):
        assert _push_on_default_branch(load_yaml(source.read_text(encoding="utf-8")), "main"), source
        break

# Manual runs accept a path, file name, stem or display name; blank means the only one.
active = {
    ".github/workflows/deploy.yml": {"name": "Deploy Worker"},
    ".github/workflows/release.yml": {"name": "Build and Release"},
}
for name in (".github/workflows/deploy.yml", "deploy.yml", "deploy", "Deploy Worker", "DEPLOY"):
    assert _resolve_workflows(active, name) == [".github/workflows/deploy.yml"], name
assert _resolve_workflows({"a.yml": {}}, "") == ["a.yml"]
for bad in ("", "missing"):
    try:
        _resolve_workflows(active, bad)
    except RuntimeError as exc:
        assert "deploy.yml" in str(exc) and "release.yml" in str(exc), exc
    else:
        raise AssertionError(f"expected a choice error for {bad!r}")

print("dispatch_manual regression test passed")

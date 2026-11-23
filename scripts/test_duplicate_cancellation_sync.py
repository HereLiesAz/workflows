#!/usr/bin/env python3
"""Registered local workflows must not cancel before the history-aware policy votes."""
from __future__ import annotations

from sync_repository import _stage_local_cancellation_policy
from sync_repository import core

PATH = ".github/workflows/ci.yml"


class FakeGitHub:
    def __init__(self, value: str):
        self.value = value
        self.calls = []

    def get_file(self, repo, path, ref=None):
        self.calls.append((repo, path, ref))
        return self.value, "source-blob"


source = """name: CI
on: push
concurrency:
  group: ci-all
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    concurrency:
      group: ci-test
      cancel-in-progress: ${{ github.event_name == 'push' }}
    steps:
      - run: |
          echo "cancel-in-progress: true"
"""
manifest = {"workflows": {PATH: {"status": "local", "ci": True}}}
unsafe = source.replace(
    'echo "cancel-in-progress: true"',
    'cancel-in-progress: true\n          echo "still a shell block"',
)
gh = FakeGitHub(unsafe)
staged = {}
updated = _stage_local_cancellation_policy(gh, "HereLiesAz/demo", "main", manifest, staged)
assert updated == [], "an additional YAML-like shell line makes text surgery unsafe"
assert staged == {}

safe = source
gh = FakeGitHub(safe)
staged = {}
updated = _stage_local_cancellation_policy(gh, "HereLiesAz/demo", "main", manifest, staged)
assert updated == [PATH], updated
text, _ = staged[PATH]
assert "  cancel-in-progress: false" in text
assert "      cancel-in-progress: false" in text
assert "ci-all" in text and "ci-test" in text
assert 'echo "cancel-in-progress: true"' in text
assert gh.calls == [("HereLiesAz/demo", PATH, "main")]

# The expected result is checked from an explicit fixture, not recomputed by the rewrite.
expected = safe.replace("  cancel-in-progress: true", "  cancel-in-progress: false").replace(
    "      cancel-in-progress: ${{ github.event_name == 'push' }}",
    "      cancel-in-progress: false",
)
assert text == expected, (text, expected)

staged = {}
assert _stage_local_cancellation_policy(
    FakeGitHub(safe), "HereLiesAz/demo", "main",
    {"workflows": {PATH: {"status": "active"}}}, staged,
) == []
assert not staged

already_safe = safe.replace("  cancel-in-progress: true", "  cancel-in-progress: false").replace(
    "      cancel-in-progress: ${{ github.event_name == 'push' }}",
    "      cancel-in-progress: false",
)
assert _stage_local_cancellation_policy(
    FakeGitHub(already_safe), "HereLiesAz/demo", "main", manifest, {},
) == []

print("local workflow cancellation policy regression test passed")

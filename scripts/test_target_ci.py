#!/usr/bin/env python3
"""Target CI stays in its own repository and is listed for ci-status reporting."""
from __future__ import annotations

from generate_event_consumers import repository_entry
from sync_repository_catalog import CI_VALIDATION_WORKFLOW, load_yaml, required_secrets, target_ci_reason

declared = load_yaml("""
name: Build
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: make test
      - uses: HereLiesAz/workflows/.github/actions/ci-report@main
""")
assert target_ci_reason(declared, None)

pr_validation = load_yaml("name: CI\non: [push, pull_request]\njobs: {t: {runs-on: x, steps: [{run: y}]}}\n")
assert target_ci_reason(pr_validation, CI_VALIDATION_WORKFLOW)
assert target_ci_reason(pr_validation, None) is None, "undeclared CI with no binding is left to the normal path"

experiment = load_yaml("name: Experiment\non: {push: {paths: [.run]}, workflow_dispatch: {}}\njobs: {t: {runs-on: x, steps: [{run: y}]}}\n")
assert target_ci_reason(experiment, CI_VALIDATION_WORKFLOW) is None, "experiments keep central compute"

assert required_secrets("${{ secrets.GOOGLE_SERVICES }} ${{ secrets.GITHUB_TOKEN }} ${{secrets.A}}") == ["A", "GOOGLE_SERVICES"]

manifest = {
    "repository": {"id": 7, "full_name": "HereLiesAz/seven"},
    "workflows": {
        ".github/workflows/ci.yml": {"status": "local", "ci": True, "name": "CI"},
        ".github/workflows/pages.yml": {"status": "local", "name": "Pages"},
    },
}
key, entry = repository_entry(manifest, lambda _: "")
assert key == "7"
assert entry["ci"] == [{"path": ".github/workflows/ci.yml", "name": "CI"}]
assert "ci" not in repository_entry({"repository": {"id": 8}, "workflows": {}}, lambda _: "")[1]
print("target CI tests passed")

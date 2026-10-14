#!/usr/bin/env python3
"""Independent scenarios for post-fix central Play checkout recovery."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from replay_failed_play import recovery_candidate, failed_checkout_run

NOW = datetime(2026, 10, 14, 3, 0, tzinfo=timezone.utc)
REPO = "HereLiesAz/CueDetat"
PATH = ".github/workflows/play_publish.yml"
FAILED_SHA = "f6da9939e5a3f65ef46eb06ae1d78b61ee1afea3"
HEAD_SHA = "4c6775e60ed0ba47b0ecea7eef659941e0ec7051"
URL = "https://github.com/HereLiesAz/workflows/actions/runs/38494133156"


class FakeGitHub:
    def __init__(self, *, changed=False, state="failure", failing_step="Checkout repository",
                 timestamp="2026-10-14T01:10:25Z", newer_status=None):
        self.changed = changed
        self.state = state
        self.failing_step = failing_step
        self.timestamp = timestamp
        self.newer_status = newer_status
        self.calls = []

    def json(self, method, path, body=None):
        self.calls.append((method, path))
        if path == f"/repos/{REPO}/commits?sha=main&per_page=15":
            return [
                {"sha": HEAD_SHA, "commit": {"message": "chore(version): 1.10.23.1 (patch) [skip ci]"}},
                {"sha": FAILED_SHA, "commit": {"message": "Merge pull request #283"}},
            ]
        if path == f"/repos/{REPO}/commits/{HEAD_SHA}/status":
            if self.newer_status is not None:
                return {"statuses": [{"context": PATH, "state": self.newer_status}]}
            return {"statuses": []}
        if path == f"/repos/{REPO}/commits/{FAILED_SHA}/status":
            return {"statuses": [{
                "context": PATH, "state": self.state,
                "target_url": URL, "updated_at": self.timestamp,
            }]}
        if path == "/repos/HereLiesAz/workflows/actions/runs/38494133156":
            return {
                "conclusion": "failure",
                "path": ".github/workflows/android-play-release.yml",
            }
        if path == "/repos/HereLiesAz/workflows/actions/runs/38494133156/jobs?per_page=100":
            return {"jobs": [{
                "name": "build_and_publish", "conclusion": "failure",
                "steps": [{"name": self.failing_step, "conclusion": "failure"}],
            }]}
        raise AssertionError(f"Unexpected API request {method} {path}")


gh = FakeGitHub()
assert recovery_candidate(gh, gh, REPO, "main", PATH, NOW) == HEAD_SHA
assert ("GET", f"/repos/{REPO}/commits/{FAILED_SHA}/status") in gh.calls
assert gh.calls[-1] == ("GET", "/repos/HereLiesAz/workflows/actions/runs/38494133156/jobs?per_page=100")

for state in ("success", "pending"):
    gh = FakeGitHub(state=state)
    assert recovery_candidate(gh, gh, REPO, "main", PATH, NOW) is None
    assert not any("/actions/runs/" in path for _, path in gh.calls)

for state in ("success", "pending"):
    gh = FakeGitHub(newer_status=state)
    assert recovery_candidate(gh, gh, REPO, "main", PATH, NOW) is None
    assert ("GET", f"/repos/{REPO}/commits/{FAILED_SHA}/status") not in gh.calls

gh = FakeGitHub(failing_step="Publish bundle to configured Play tracks")
assert recovery_candidate(gh, gh, REPO, "main", PATH, NOW) is None

gh = FakeGitHub(timestamp="2026-10-01T01:10:25Z")
assert recovery_candidate(gh, gh, REPO, "main", PATH, NOW) is None

gh = FakeGitHub()
assert not failed_checkout_run(gh, "https://github.com/attacker/workflows/actions/runs/38494133156")
assert not gh.calls

# A fresh code commit without status blocks recovery, rather than incorrectly
# releasing unverified content or a superseded revision.
class NewCode(FakeGitHub):
    def json(self, method, path, body=None):
        if path == f"/repos/{REPO}/commits?sha=main&per_page=15":
            return [{"sha": HEAD_SHA, "commit": {"message": "Change game logic"}},
                    {"sha": FAILED_SHA, "commit": {"message": "Previous failure"}}]
        return super().json(method, path, body)

assert recovery_candidate(NewCode(), FakeGitHub(), REPO, "main", PATH, NOW) is None
# A real registered, active source is the only route to a gateway retry. Check the
# complete dispatch payload instead of deriving it through the implementation.
import json
import tempfile
from pathlib import Path
import replay_failed_play as replay_module

class RegistryTarget(FakeGitHub):
    def json(self, method, path, body=None):
        if path == f"/repos/{REPO}":
            return {
                "id": 988574413, "private": False, "default_branch": "main",
                "owner": {"id": 103241502, "login": "HereLiesAz"},
            }
        return super().json(method, path, body)

class Central(RegistryTarget):
    def __init__(self):
        super().__init__()
        self.dispatched = []

    def json(self, method, path, body=None):
        if method == "POST":
            self.dispatched.append((path, body))
            return None
        return super().json(method, path, body)

with tempfile.TemporaryDirectory() as scratch:
    original_root = replay_module.ROOT
    try:
        replay_module.ROOT = Path(scratch)
        registry = replay_module.ROOT / "registry" / "988574413"
        registry.mkdir(parents=True)
        (registry / "source.yml").write_text(
            "on:\\n  push:\\n    branches: 'main'\\n".replace("\\n", "\n"),
            encoding="utf-8",
        )
        (registry / "manifest.json").write_text(json.dumps({
            "repository": {
                "owner_id": 103241502, "owner_login": "HereLiesAz",
                "full_name": REPO, "id": 988574413,
            },
            "workflows": {PATH: {
                "status": "active",
                "central_workflow": ".github/workflows/android-play-release.yml",
                "registry_source": "registry/988574413/source.yml",
            }},
        }), encoding="utf-8")
        central = Central()
        results = replay_module.replay(RegistryTarget(), central, NOW)
        assert results == [{"repository": REPO, "source": PATH, "sha": HEAD_SHA}]
        assert central.dispatched == [(
            "/repos/HereLiesAz/workflows/actions/workflows/gateway.yml/dispatches",
            {
                "ref": "main",
                "inputs": {
                    "repository": REPO, "source_workflow_path": PATH,
                    "target_ref": HEAD_SHA, "inputs_json": '{"dry_run":false}',
                },
            },
        )]

        # An already-successful release must never dispatch a new Play upload.
        central = Central()
        assert replay_module.replay(RegistryTarget(state="success"), central, NOW) == []
        assert central.dispatched == []
    finally:
        replay_module.ROOT = original_root

# The controller's recovery is a separate runner job; the validation job's
# installed Python packages are not present in that job. A green test job does
# not prove recovery can import dispatch_manual (and hence ruamel.yaml).
from sync_repository_catalog import load_yaml

controller = load_yaml(
    (Path(__file__).resolve().parents[1] / ".github/workflows/validate-controller.yml")
    .read_text(encoding="utf-8")
)
recovery_steps = controller["jobs"]["replay-failed-play"]["steps"]
install_idx, install_step = next(
    (i, step) for i, step in enumerate(recovery_steps)
    if step.get("name") == "Install Play recovery Python dependencies"
)
python_idx = next(
    i for i, step in enumerate(recovery_steps)
    if str(step.get("uses") or "").startswith("actions/setup-python@")
)
run_idx = next(
    i for i, step in enumerate(recovery_steps)
    if step.get("name") == "Replay verified prior Play checkout failures"
)
assert python_idx < install_idx < run_idx
assert "ruamel.yaml==0.18.15" in install_step["run"]
assert install_step["if"] == recovery_steps[run_idx]["if"]

# A repair to the recovery job itself must trigger recovery on the next merge.
# Previously only edits to the publisher/script were checked; the dependency
# installation fix changed validate-controller.yml and silently skipped replay.
detect_step = next(step for step in recovery_steps if step.get("name") == "Detect publisher or recovery runner changes")
assert ".github/workflows/validate-controller.yml" in detect_step["run"]
assert "scripts/replay_failed_play.py" in detect_step["run"]
assert ".github/workflows/android-play-release.yml" in detect_step["run"]

print("Play checkout replay regression test passed")

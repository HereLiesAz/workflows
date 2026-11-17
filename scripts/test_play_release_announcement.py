#!/usr/bin/env python3
"""Regression tests for the Play release announcement (run from the repository root).

After a successful, non-deferred Play publish, .github/workflows/android-play-release.yml files one
CLOSED issue in the target repository, labelled play-release and titled
"Play release <versionName> (<versionCode>)", so an app can tell that Google Play has a new build
(the public store page only shows production, and Play Core does not run on Android TV). Checks:
  * the step exists, runs after the publish, only when it succeeded and was not deferred or a pull
    request, never fails the release, and uses the target repository's token;
  * a new build creates the label, the issue, and closes it, with the title and tracks the app reads;
  * a build that was already announced is not announced twice (re-runs);
  * without a release version it does nothing.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/android-play-release.yml"
document = YAML(typ="safe").load(WORKFLOW.read_text(encoding="utf-8"))
steps = document["jobs"]["build_and_publish"]["steps"]
names = [step.get("name") for step in steps]

assert "Announce Play release" in names, names
announce = steps[names.index("Announce Play release")]
assert names.index("Announce Play release") > names.index("Publish bundle to configured Play tracks"), "announce before publish"

condition = announce["if"]
assert "steps.play.outcome == 'success'" in condition, condition
assert "env.PLAY_DEFERRED != 'true'" in condition, condition
assert "inputs.target_event_name != 'pull_request'" in condition, condition
assert announce.get("continue-on-error") is True, "a failed announcement must not fail the release"
assert announce["env"]["GH_TOKEN"] == "${{ steps.target-token.outputs.token }}", announce["env"]
script = announce["run"]
assert 'label="play-release"' in script
assert "state_reason=completed" in script and "state=closed" in script, "the issue must be closed"

FAKE_GH = r'''#!/usr/bin/env bash
# Records every call; answers the two reads the script makes.
printf '%s\0' "$*" >> "$GH_LOG"
case "$*" in
  *"--method POST"*"/issues"*) echo 7 ;;
  *"--method"*) ;;
  *"issues?state=all"*) cat "$GH_EXISTING" ;;
esac
'''


def run(env_extra: dict[str, str], existing: list[dict]) -> tuple[int, list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        gh = tmp_path / "gh"
        gh.write_text(FAKE_GH, encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
        (tmp_path / "existing.json").write_text(json.dumps(existing), encoding="utf-8")
        log = tmp_path / "calls.log"
        log.write_text("", encoding="utf-8")
        env = {
            "PATH": f"{tmp}:{os.environ['PATH']}",
            "GH_LOG": str(log),
            "GH_EXISTING": str(tmp_path / "existing.json"),
            "TARGET_REPOSITORY": "HereLiesAz/app",
            "TARGET_SHA": "abc123",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_REPOSITORY": "HereLiesAz/workflows",
            "GITHUB_RUN_ID": "42",
            "ANNOUNCE_PACKAGE_NAME": "com.example.app",
            "TRACKS_JSON": json.dumps([{"track": "internal", "status": "completed"}, {"track": "alpha", "status": "draft"}]),
            "EFFECTIVE_RELEASE_VERSION_NAME": "0.18.2.1",
            "EFFECTIVE_RELEASE_VERSION_CODE": "110080066",
            **env_extra,
        }
        result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout, result.stderr, file=sys.stderr)
        return result.returncode, [c for c in log.read_text(encoding="utf-8").split("\0") if c]


# A new build: label, issue, close.
code, calls = run({}, existing=[])
assert code == 0
assert any("--method POST repos/HereLiesAz/app/labels" in c and "name=play-release" in c for c in calls), calls
issue = [c for c in calls if "--method POST repos/HereLiesAz/app/issues" in c]
assert len(issue) == 1, calls
assert "title=Play release 0.18.2.1 (110080066)" in issue[0], issue[0]
assert "labels[]=play-release" in issue[0], issue[0]
assert "internal (completed), alpha (draft)" in issue[0], issue[0]
assert "com.example.app" in issue[0] and '"versionCode":110080066' in issue[0], issue[0]
assert any("--method PATCH repos/HereLiesAz/app/issues/7" in c and "state=closed" in c for c in calls), calls

# Already announced (a re-run of the same build): nothing is created.
code, calls = run({}, existing=[{"number": 5, "title": "Play release 0.18.2.1 (110080066)"}])
assert code == 0
assert not any("--method" in c for c in calls), calls

# A different build is announced even when others are on file.
code, calls = run({}, existing=[{"number": 5, "title": "Play release 0.18.1.1 (110080065)"}])
assert code == 0
assert any("--method POST repos/HereLiesAz/app/issues" in c for c in calls), calls

# No release version: skipped without error and without calls.
code, calls = run({"EFFECTIVE_RELEASE_VERSION_CODE": ""}, existing=[])
assert code == 0
assert calls == [], calls

print("Play release announcement checks passed")

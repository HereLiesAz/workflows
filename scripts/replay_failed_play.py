#!/usr/bin/env python3
"""Safely replay failed centralized Play *checkouts* after a publisher repair.

A green target-repository hand-off is not evidence of publication. This recovery
runs only after a validated central publisher change. It never changes target
repositories and never retries a build that reached publishing.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dispatch_manual import _push_on_default_branch
from sync_repository_catalog import (
    CENTRAL_REPOSITORY,
    OWNER_ID,
    OWNER_LOGIN,
    GitHub,
    load_yaml,
)

ROOT = Path(__file__).resolve().parents[1]
PLAY_WORKFLOW = ".github/workflows/android-play-release.yml"
FAILURE_URL = re.compile(
    r"^https://github[.]com/HereLiesAz/workflows/actions/runs/([0-9]+)$",
    re.IGNORECASE,
)
RECOVERY_WINDOW = timedelta(days=7)


def failed_checkout_run(central_gh: GitHub, target_url: str) -> bool:
    """Accept only completed central runs failing at target checkout, before Play upload."""
    match = FAILURE_URL.fullmatch(target_url)
    if not match:
        return False
    run_id = match.group(1)
    run = central_gh.json("GET", f"/repos/{CENTRAL_REPOSITORY}/actions/runs/{run_id}")
    if (run or {}).get("conclusion") != "failure":
        return False
    if (run or {}).get("path") != PLAY_WORKFLOW:
        return False
    jobs = central_gh.json(
        "GET", f"/repos/{CENTRAL_REPOSITORY}/actions/runs/{run_id}/jobs?per_page=100"
    ).get("jobs", [])
    return any(
        job.get("name") == "build_and_publish"
        and job.get("conclusion") == "failure"
        and any(
            step.get("name") == "Checkout repository"
            and step.get("conclusion") == "failure"
            for step in job.get("steps", [])
        )
        for job in jobs
    )


def recovery_candidate(
    gh: GitHub,
    central_gh: GitHub,
    repository: str,
    default_branch: str,
    source_path: str,
    now: datetime,
) -> str | None:
    """Return current immutable SHA only if its last release failed in checkout.

    Ignore a newer generated version bump, never a newer untested code change.
    A newer successful/pending release status always wins over an older failure.
    """
    commits = gh.json(
        "GET", f"/repos/{repository}/commits?sha={default_branch}&per_page=15"
    )
    if not commits:
        return None
    head_sha = str(commits[0]["sha"])
    for commit in commits:
        sha = str(commit["sha"])
        statuses = gh.json("GET", f"/repos/{repository}/commits/{sha}/status")
        matching = next(
            (s for s in statuses.get("statuses", []) if s.get("context") == source_path),
            None,
        )
        if matching is not None:
            if matching.get("state") != "failure":
                return None
            modified = datetime.fromisoformat(
                str(matching["updated_at"]).replace("Z", "+00:00")
            )
            if not (timedelta(0) <= now - modified <= RECOVERY_WINDOW):
                return None
            if not failed_checkout_run(central_gh, str(matching.get("target_url") or "")):
                return None
            return head_sha

        message = str((commit.get("commit") or {}).get("message") or "").split("\n", 1)[0]
        if not (message.startswith("chore(version):") and "[skip ci]" in message):
            # A newer real code change has no Play status yet: never race its release.
            return None
    return None


def replay(gh: GitHub, central_gh: GitHub, now: datetime) -> list[dict[str, str]]:
    """Recover active Play bindings, not an invented hard-coded list of projects."""
    dispatched = []
    for manifest_path in sorted((ROOT / "registry").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        identity = manifest.get("repository") or {}
        if identity.get("owner_id") != OWNER_ID:
            continue
        if str(identity.get("owner_login") or "").casefold() != OWNER_LOGIN.casefold():
            continue
        repository = str(identity.get("full_name") or "")
        if not repository.startswith(OWNER_LOGIN + "/"):
            continue
        for source_path, entry in sorted((manifest.get("workflows") or {}).items()):
            if not isinstance(entry, dict) or entry.get("status") != "active":
                continue
            if entry.get("central_workflow") != PLAY_WORKFLOW:
                continue

            doc_path = ROOT / str(entry.get("registry_source") or "")
            if not doc_path.is_file():
                raise RuntimeError(f"Missing active source: {doc_path}")
            source_doc = load_yaml(doc_path.read_text(encoding="utf-8"))
            repo = gh.json("GET", f"/repos/{repository}")
            if repo.get("private") or repo.get("id") != identity.get("id"):
                continue
            if int((repo.get("owner") or {}).get("id") or 0) != OWNER_ID:
                continue
            branch = str(repo.get("default_branch") or "")
            if not branch or not _push_on_default_branch(source_doc, branch):
                continue
            head_sha = recovery_candidate(
                gh, central_gh, repository, branch, source_path, now
            )
            if head_sha is None:
                continue

            # Dispatch through the existing gateway; it revalidates registry, profile,
            # owner and source SHA. This creates a *new* run using the fixed publisher.
            inputs = {
                "repository": repository,
                "source_workflow_path": source_path,
                "target_ref": head_sha,
                "inputs_json": '{"dry_run":false}',
            }
            central_gh.json(
                "POST",
                f"/repos/{CENTRAL_REPOSITORY}/actions/workflows/gateway.yml/dispatches",
                {"ref": "main", "inputs": inputs},
            )
            dispatched.append({"repository": repository, "source": source_path, "sha": head_sha})
            print(f"Replaying {repository}:{source_path} at {head_sha}")
    return dispatched


def main() -> int:
    target_gh = GitHub(os.environ.get("GH_TOKEN", ""))
    central_gh = GitHub(os.environ.get("CENTRAL_GITHUB_TOKEN", ""))
    dispatched = replay(target_gh, central_gh, datetime.now(timezone.utc))
    print(json.dumps({"replayed": dispatched}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

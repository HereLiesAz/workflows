#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ruamel.yaml import YAML

from dispatch_request import _dispatch_entry
from sync_repository import GitHub, OWNER_ID, OWNER_LOGIN

ROOT = Path(__file__).resolve().parents[1]


def schedule_crons(source_path: Path) -> list[str]:
    doc = YAML(typ="safe").load(source_path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        return []
    on_value = doc.get("on")
    if not isinstance(on_value, dict):
        return []
    schedule = on_value.get("schedule")
    if not isinstance(schedule, list):
        return []
    result: list[str] = []
    for item in schedule:
        if isinstance(item, dict) and item.get("cron"):
            result.append(str(item["cron"]).strip())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch registered workflows for one exact cron expression.")
    parser.add_argument("--schedule", required=True)
    args = parser.parse_args()

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "")
    actor = os.environ.get("GITHUB_ACTOR", OWNER_LOGIN)
    actor_id = os.environ.get("GITHUB_ACTOR_ID", str(OWNER_ID))

    results: list[dict] = []
    for manifest_path in sorted((ROOT / "registry").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        repository_meta = manifest.get("repository") or {}
        repository = str(repository_meta.get("full_name") or "")
        repository_id = str(repository_meta.get("id") or "")
        if not repository or not repository_id:
            continue

        repo = gh.repo(repository)
        if repo.get("archived") is True:
            continue
        default_branch = str(repo.get("default_branch") or repository_meta.get("default_branch") or "main")
        commit = gh.json("GET", f"/repos/{repository}/commits/{default_branch}")
        target_sha = str((commit or {}).get("sha") or "")
        if not target_sha:
            raise RuntimeError(f"Could not resolve {repository}:{default_branch}")

        for source_workflow_path, entry in sorted((manifest.get("workflows") or {}).items()):
            if not isinstance(entry, dict) or entry.get("status") != "active":
                continue
            registry_source = str(entry.get("registry_source") or "")
            if not registry_source:
                continue
            source_path = ROOT / registry_source
            if not source_path.is_file() or args.schedule not in schedule_crons(source_path):
                continue

            request = {
                "repository": repository,
                "repository_id": repository_id,
                "repository_owner": str(repo["owner"]["login"]),
                "repository_owner_id": str(repo["owner"]["id"]),
                "sha": target_sha,
                "check_sha": target_sha,
                "ref": f"refs/heads/{default_branch}",
                "ref_name": default_branch,
                "ref_type": "branch",
                "head_ref": "",
                "base_ref": "",
                "actor": actor,
                "actor_id": actor_id,
                "event_name": "schedule",
                "event": {"schedule": args.schedule},
                "inputs": {},
                "vars": {},
                "run_id": f"schedule-{run_id}",
                "run_number": run_number,
                "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
                "workflow_ref": "",
                "workflow_name": str(entry.get("name") or source_workflow_path),
                "source_workflow_path": source_workflow_path,
                "source_sha256": str(entry.get("source_sha256") or ""),
            }
            results.append(
                _dispatch_entry(
                    gh,
                    request,
                    repository,
                    repository_id,
                    source_workflow_path,
                    entry,
                    "schedule",
                )
            )

    print(
        json.dumps(
            {
                "status": "scheduled-routing-complete",
                "schedule": args.schedule,
                "dispatch_count": sum(1 for item in results if item.get("status") == "dispatched"),
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

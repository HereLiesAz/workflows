#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

from dispatch_request import _dispatch_entry
from sync_repository import GitHub, OWNER_ID, OWNER_LOGIN, load_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Manually invoke one registered centralized workflow.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-workflow-path", required=True)
    parser.add_argument("--target-ref", default="")
    parser.add_argument("--inputs-json", default="{}")
    args = parser.parse_args()

    try:
        supplied_inputs = json.loads(args.inputs_json or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"inputs-json is invalid JSON: {exc}") from exc
    if not isinstance(supplied_inputs, dict):
        raise RuntimeError("inputs-json must be a JSON object")

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    repo = gh.repo(args.repository)
    repository_id = str(repo["id"])
    if int(repo["owner"]["id"]) != OWNER_ID or str(repo["owner"]["login"]).casefold() != OWNER_LOGIN.casefold():
        raise RuntimeError("Repository is not owned by HereLiesAz")

    manifest = load_manifest(gh, int(repository_id))
    entry = (manifest.get("workflows") or {}).get(args.source_workflow_path)
    if not isinstance(entry, dict):
        raise RuntimeError(f"Workflow is not registered: {args.source_workflow_path}")
    if entry.get("status") != "active":
        raise RuntimeError(f"Workflow is not active: {args.source_workflow_path} ({entry.get('status')})")

    target_ref = args.target_ref.strip() or str(repo.get("default_branch") or "main")
    commit = gh.json("GET", f"/repos/{args.repository}/commits/{target_ref}")
    target_sha = str((commit or {}).get("sha") or "")
    if not target_sha:
        raise RuntimeError(f"Could not resolve {args.repository}:{target_ref}")

    default_branch = str(repo.get("default_branch") or "main")
    ref_name = target_ref
    ref = target_ref if target_ref.startswith("refs/") else f"refs/heads/{target_ref}"
    if target_ref == target_sha:
        ref = f"refs/heads/{default_branch}"
        ref_name = default_branch

    request = {
        "repository": args.repository,
        "repository_id": repository_id,
        "repository_owner": str(repo["owner"]["login"]),
        "repository_owner_id": str(repo["owner"]["id"]),
        "sha": target_sha,
        "check_sha": target_sha,
        "ref": ref,
        "ref_name": ref_name,
        "ref_type": "branch",
        "head_ref": "",
        "base_ref": "",
        "actor": os.environ.get("GITHUB_ACTOR", OWNER_LOGIN),
        "actor_id": os.environ.get("GITHUB_ACTOR_ID", str(OWNER_ID)),
        "event_name": "workflow_dispatch",
        "event": {"inputs": supplied_inputs},
        "inputs": supplied_inputs,
        "vars": {},
        "run_id": f"manual-{os.environ.get('GITHUB_RUN_ID', '')}",
        "run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        "workflow_ref": "",
        "workflow_name": str(entry.get("name") or args.source_workflow_path),
        "source_workflow_path": args.source_workflow_path,
        "source_sha256": str(entry.get("source_sha256") or ""),
    }

    result = _dispatch_entry(
        gh,
        request,
        args.repository,
        repository_id,
        args.source_workflow_path,
        entry,
        "workflow_dispatch",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

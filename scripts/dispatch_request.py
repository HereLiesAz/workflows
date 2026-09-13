#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse

from sync_repository import (
    CENTRAL_REPOSITORY,
    GitHub,
    OWNER_ID,
    OWNER_LOGIN,
    ApiError,
    load_manifest,
)


def require(value: str, name: str) -> str:
    if value is None or value == "":
        raise RuntimeError(f"Missing required dispatch field: {name}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and dispatch an absorbed central workflow.")
    parser.add_argument("--request", required=True, help="JSON request file")
    args = parser.parse_args()

    with open(args.request, "r", encoding="utf-8") as handle:
        request = json.load(handle)

    gh = GitHub(os.environ.get("GH_TOKEN", ""))

    repository = require(str(request.get("repository", "")), "repository")
    repository_id = require(str(request.get("repository_id", "")), "repository_id")
    source_path = require(str(request.get("source_workflow_path", "")), "source_workflow_path")
    source_sha256 = require(str(request.get("source_sha256", "")), "source_sha256")

    repo = gh.repo(repository)
    if str(repo["id"]) != repository_id:
        raise RuntimeError("Repository ID mismatch")
    if int(repo["owner"]["id"]) != OWNER_ID or repo["owner"]["login"].lower() != OWNER_LOGIN.lower():
        raise RuntimeError("Repository is not owned by HereLiesAz")

    manifest = load_manifest(gh, int(repository_id))
    manifest_repo = manifest.get("repository") or {}
    if str(manifest_repo.get("id")) != repository_id:
        raise RuntimeError("Registry repository ID mismatch")
    if str(manifest_repo.get("owner_id")) != str(OWNER_ID):
        raise RuntimeError("Registry owner ID mismatch")

    entry = (manifest.get("workflows") or {}).get(source_path)
    if not entry:
        raise RuntimeError(f"Workflow is not registered: {source_path}")
    if entry.get("status") != "active":
        raise RuntimeError(f"Workflow is not active: {source_path} ({entry.get('status')})")
    if entry.get("source_sha256") != source_sha256:
        raise RuntimeError("Proxy source hash does not match the central registry")

    central_workflow = require(str(entry.get("central_workflow", "")), "central_workflow")
    workflow_id = urllib.parse.quote(central_workflow.rsplit("/", 1)[-1], safe="")

    dispatch_inputs = {
        "target_repository": repository,
        "target_repository_id": repository_id,
        "target_repository_owner": require(str(request.get("repository_owner", "")), "repository_owner"),
        "target_repository_owner_id": require(str(request.get("repository_owner_id", "")), "repository_owner_id"),
        "target_sha": require(str(request.get("sha", "")), "sha"),
        "target_check_sha": require(str(request.get("check_sha", "")), "check_sha"),
        "target_ref": require(str(request.get("ref", "")), "ref"),
        "target_ref_name": str(request.get("ref_name", "")),
        "target_ref_type": str(request.get("ref_type", "")),
        "target_head_ref": str(request.get("head_ref", "")),
        "target_base_ref": str(request.get("base_ref", "")),
        "target_actor": require(str(request.get("actor", "")), "actor"),
        "target_actor_id": str(request.get("actor_id", "")),
        "target_event_name": require(str(request.get("event_name", "")), "event_name"),
        "target_event_json": json.dumps(request.get("event") or {}, separators=(",", ":")),
        "target_inputs_json": json.dumps(request.get("inputs") or {}, separators=(",", ":")),
        "target_vars_json": json.dumps(request.get("vars") or {}, separators=(",", ":")),
        "target_run_id": require(str(request.get("run_id", "")), "run_id"),
        "target_run_number": str(request.get("run_number", "")),
        "target_run_attempt": str(request.get("run_attempt", "")),
        "target_workflow_ref": str(request.get("workflow_ref", "")),
        "target_workflow_name": require(str(request.get("workflow_name", "")), "workflow_name"),
        "source_workflow_path": source_path,
        "source_sha256": source_sha256,
    }

    body = {"ref": "main", "inputs": dispatch_inputs}
    endpoint = f"/repos/{CENTRAL_REPOSITORY}/actions/workflows/{workflow_id}/dispatches"

    last_error: Exception | None = None
    for delay in (0, 1, 2, 4):
        if delay:
            time.sleep(delay)
        try:
            response = gh.json("POST", endpoint, body)
            print(json.dumps({
                "status": "dispatched",
                "repository": repository,
                "source_workflow": source_path,
                "central_workflow": central_workflow,
                "dispatch_response": response,
            }, indent=2, sort_keys=True))
            return 0
        except ApiError as exc:
            last_error = exc
            if "-> 404:" not in str(exc):
                raise

    raise RuntimeError(f"Central workflow did not become dispatchable: {last_error}")


if __name__ == "__main__":
    raise SystemExit(main())

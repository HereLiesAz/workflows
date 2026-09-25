#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import PurePosixPath

from dispatch_request import _dispatch_entry
from sync_repository import GitHub, OWNER_ID, OWNER_LOGIN, load_manifest
from sync_repository_catalog import CENTRAL_REPOSITORY, load_yaml


def _push_on_default_branch(source_doc: dict, default_branch: str) -> bool:
    """True when the source workflow runs on pushes to the default branch."""
    on_value = source_doc.get("on", source_doc.get(True))
    if on_value == "push" or (isinstance(on_value, list) and "push" in on_value):
        return True
    if not isinstance(on_value, dict) or "push" not in on_value:
        return False
    push = on_value.get("push") or {}
    branches = push.get("branches") if isinstance(push, dict) else None
    if not branches:
        return not (isinstance(push, dict) and push.get("tags"))
    return any(fnmatch.fnmatch(default_branch, str(pattern)) for pattern in branches)


def _resolve_workflows(active: dict, requested: str) -> list[str]:
    """Match a path, file name, stem or display name; blank means the only workflow."""
    if not requested:
        if len(active) == 1:
            return list(active)
        raise RuntimeError("Choose a workflow: " + ", ".join(sorted(active)))
    wanted = requested.strip().casefold()
    matches = [
        path for path, entry in active.items()
        if wanted in {
            path.casefold(),
            PurePosixPath(path).name.casefold(),
            PurePosixPath(path).stem.casefold(),
            str(entry.get("name") or "").casefold(),
        }
    ]
    if not matches:
        raise RuntimeError(f"No active workflow matches {requested!r}. Available: " + ", ".join(sorted(active)))
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description="Manually invoke registered centralized workflows.")
    parser.add_argument("--repository", required=True, help="name or owner/name")
    parser.add_argument("--source-workflow-path", default="", help="path, file name, stem or display name")
    parser.add_argument("--target-ref", default="")
    parser.add_argument("--inputs-json", default="{}")
    parser.add_argument(
        "--catch-up",
        action="store_true",
        help="run every workflow that triggers on pushes to the default branch (after first registration)",
    )
    args = parser.parse_args()

    try:
        supplied_inputs = json.loads(args.inputs_json or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"inputs-json is invalid JSON: {exc}") from exc
    if not isinstance(supplied_inputs, dict):
        raise RuntimeError("inputs-json must be a JSON object")

    repository = args.repository.strip()
    if "/" not in repository:
        repository = f"{OWNER_LOGIN}/{repository}"

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    repo = gh.repo(repository)
    repository_id = str(repo["id"])
    if int(repo["owner"]["id"]) != OWNER_ID or str(repo["owner"]["login"]).casefold() != OWNER_LOGIN.casefold():
        raise RuntimeError("Repository is not owned by HereLiesAz")

    manifest = load_manifest(gh, int(repository_id))
    active = {
        path: entry
        for path, entry in (manifest.get("workflows") or {}).items()
        if isinstance(entry, dict) and entry.get("status") == "active"
    }
    default_branch = str(repo.get("default_branch") or "main")
    if args.catch_up:
        selected = []
        for path, entry in sorted(active.items()):
            source_text, _ = gh.get_file(CENTRAL_REPOSITORY, str(entry.get("registry_source") or ""))
            source_doc = load_yaml(source_text)
            if isinstance(source_doc, dict) and _push_on_default_branch(source_doc, default_branch):
                selected.append(path)
        if not selected:
            print(json.dumps({"status": "nothing-to-run", "repository": repository}))
            return 0
    else:
        selected = _resolve_workflows(active, args.source_workflow_path)

    results = [
        _run_one(gh, repo, repository, repository_id, path, active[path], args.target_ref, supplied_inputs)
        for path in selected
    ]
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


def _run_one(gh, repo, repository, repository_id, source_workflow_path, entry, target_ref_arg, supplied_inputs):
    target_ref = target_ref_arg.strip() or str(repo.get("default_branch") or "main")
    commit = gh.json("GET", f"/repos/{repository}/commits/{target_ref}")
    target_sha = str((commit or {}).get("sha") or "")
    if not target_sha:
        raise RuntimeError(f"Could not resolve {repository}:{target_ref}")

    default_branch = str(repo.get("default_branch") or "main")
    ref_name = target_ref
    ref = target_ref if target_ref.startswith("refs/") else f"refs/heads/{target_ref}"
    if target_ref == target_sha:
        ref = f"refs/heads/{default_branch}"
        ref_name = default_branch

    request = {
        "repository": repository,
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
        "workflow_name": str(entry.get("name") or source_workflow_path),
        "source_workflow_path": source_workflow_path,
        "source_sha256": str(entry.get("source_sha256") or ""),
    }

    result = _dispatch_entry(
        gh,
        request,
        repository,
        repository_id,
        source_workflow_path,
        entry,
        "workflow_dispatch",
    )
    return result


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.parse

try:
    from . import sync_repository_catalog as core
    from .sync_repository_catalog import *  # noqa: F401,F403
except ImportError:
    import sync_repository_catalog as core
    from sync_repository_catalog import *  # noqa: F401,F403


_base_compile_central = core.compile_central
_base_build_proxy = core.build_proxy


def compile_central(source_text: str, target: dict, source_path: str, check_name: str) -> str:
    compiled = _base_compile_central(source_text, target, source_path, check_name)
    compiled = (
        compiled
        .replace("__central_check_start", "central_check_start")
        .replace("__central_check_finish", "central_check_finish")
    )

    doc = load_yaml(compiled)
    jobs = doc.get("jobs") or {}
    start = jobs.get("central_check_start")
    finish = jobs.get("central_check_finish")
    if not isinstance(start, dict) or not isinstance(finish, dict):
        raise ValueError("compiled workflow is missing central reporting jobs")

    start.pop("outputs", None)
    start_steps = start.get("steps") or []
    if not start_steps:
        raise ValueError("compiled workflow is missing target identity validation")
    start["steps"] = [
        start_steps[0],
        {
            "name": "Set target status pending",
            "env": {
                "GH_TOKEN": "${{ secrets.GH_TOKEN }}",
                "STATUS_CONTEXT": "${{ inputs.source_workflow_path }}",
                "DETAILS_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
            },
            "shell": "bash",
            "run": '''set -euo pipefail
payload="$(jq -n --arg state "pending" --arg context "$STATUS_CONTEXT" --arg description "Running from the shared HereLiesAz/workflows catalog." --arg target_url "$DETAILS_URL" '{state:$state,context:$context,description:$description,target_url:$target_url}')"
gh api --method POST "repos/${TARGET_REPOSITORY}/statuses/${TARGET_CHECK_SHA}" --input - <<<"$payload"''',
        },
    ]

    finish["steps"] = [
        {
            "name": "Complete target status",
            "env": {
                "GH_TOKEN": "${{ secrets.GH_TOKEN }}",
                "STATUS_CONTEXT": "${{ inputs.source_workflow_path }}",
                "FAILED": "${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}",
                "DETAILS_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
            },
            "shell": "bash",
            "run": '''set -euo pipefail
if [[ "$FAILED" == "true" ]]; then
  state="failure"
  description="Shared catalog workflow failed."
else
  state="success"
  description="Shared catalog workflow completed successfully."
fi
payload="$(jq -n --arg state "$state" --arg context "$STATUS_CONTEXT" --arg description "$description" --arg target_url "$DETAILS_URL" '{state:$state,context:$context,description:$description,target_url:$target_url}')"
gh api --method POST "repos/${TARGET_REPOSITORY}/statuses/${TARGET_CHECK_SHA}" --input - <<<"$payload"''',
        }
    ]

    return dump_yaml(doc)


def build_proxy(source_text: str, source_path: str, source_hash: str, workflow_name: str) -> str:
    proxy = _base_build_proxy(source_text, source_path, source_hash, workflow_name)
    if source_path != ".github/workflows/jules-dispatch.yml":
        return proxy

    needle = "  central-dispatch:\n    runs-on: ubuntu-latest\n"
    replacement = """  central-dispatch:
    if: >-
      ${{
        github.event_name == 'issues' ||
        github.event_name == 'pull_request' ||
        (github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '@jules')) ||
        (github.event_name == 'pull_request_review_comment' && startsWith(github.event.comment.body, '@jules')) ||
        (github.event_name == 'pull_request_review' && startsWith(github.event.review.body, '@jules'))
      }}
    runs-on: ubuntu-latest
"""
    if needle not in proxy:
        raise ValueError("generated Jules proxy shape changed; cannot apply comment gate")
    return proxy.replace(needle, replacement, 1)


# The core synchronizer resolves these globals at runtime, so patching them here
# makes every generated shared workflow use GitHub-safe IDs, PAT-compatible commit
# statuses, and the same Jules event gate as the curated implementation.
core.compile_central = compile_central
core.build_proxy = build_proxy


def _load_policy(gh: GitHub, repo_id: int) -> dict:
    try:
        text, _ = gh.get_file(CENTRAL_REPOSITORY, f"registry/{repo_id}/policy.json")
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except ApiError as exc:
        if "-> 404:" in str(exc):
            return {}
        raise


def _preflight_catalog(gh: GitHub, repo: dict, policy: dict) -> None:
    disabled = {str(path) for path in (policy.get("disabled_workflows") or [])}
    missing = []
    for source_path, catalog_path in core.CATALOG_PATH_OVERRIDES.items():
        if source_path in disabled:
            continue
        try:
            gh.contents(repo["full_name"], source_path)
        except ApiError as exc:
            if "-> 404:" in str(exc):
                continue
            raise
        try:
            gh.get_file(CENTRAL_REPOSITORY, catalog_path)
        except ApiError as exc:
            if "-> 404:" in str(exc):
                missing.append(catalog_path)
            else:
                raise
    if missing:
        raise RuntimeError("Missing curated catalog workflows: " + ", ".join(sorted(missing)))


def _apply_disabled_workflows(gh: GitHub, repo: dict, policy: dict, dry_run: bool) -> list[dict]:
    results = []
    disabled = policy.get("disabled_workflows") or []
    if not isinstance(disabled, list):
        raise RuntimeError("policy disabled_workflows must be a list")

    for path in disabled:
        path = str(path)
        try:
            item = gh.contents(repo["full_name"], path)
        except ApiError as exc:
            if "-> 404:" in str(exc):
                continue
            raise
        if not isinstance(item, dict) or item.get("type") != "file":
            continue
        results.append({"path": path, "status": "would-delete" if dry_run else "deleted"})
        if dry_run:
            continue
        quoted = urllib.parse.quote(path, safe="/")
        gh.json(
            "DELETE",
            f"/repos/{repo['full_name']}/contents/{quoted}",
            {
                "message": f"Remove disabled workflow {path}",
                "sha": item["sha"],
                "branch": repo["default_branch"],
            },
        )
    return results


def _delete_central_file(gh: GitHub, path: str, message: str) -> bool:
    try:
        item = gh.contents(CENTRAL_REPOSITORY, path)
    except ApiError as exc:
        if "-> 404:" in str(exc):
            return False
        raise
    if not isinstance(item, dict) or item.get("type") != "file":
        return False
    quoted = urllib.parse.quote(path, safe="/")
    gh.json(
        "DELETE",
        f"/repos/{CENTRAL_REPOSITORY}/contents/{quoted}",
        {"message": message, "sha": item["sha"], "branch": "main"},
    )
    return True


def _finalize_registry_and_gc(gh: GitHub, repo: dict, policy: dict) -> list[str]:
    repo_id = int(repo["id"])
    manifest = core.load_manifest(gh, repo_id)
    workflows = manifest.get("workflows") or {}
    disabled = {str(path) for path in (policy.get("disabled_workflows") or [])}
    removed_registry_sources = []

    for path in list(disabled):
        entry = workflows.pop(path, None)
        if isinstance(entry, dict) and entry.get("registry_source"):
            source_path = str(entry["registry_source"])
            if _delete_central_file(gh, source_path, f"Remove disabled workflow source {path}"):
                removed_registry_sources.append(source_path)

    manifest["workflows"] = workflows
    gh.put_file(
        CENTRAL_REPOSITORY,
        core.manifest_path(repo_id),
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        f"Apply workflow policy for {repo['full_name']}",
        branch="main",
    )

    active_refs = {
        str(entry.get("central_workflow"))
        for entry in workflows.values()
        if isinstance(entry, dict) and entry.get("status") == "active" and entry.get("central_workflow")
    }
    listing = gh.contents(CENTRAL_REPOSITORY, ".github/workflows")
    deleted_legacy = []
    prefix = f".github/workflows/absorbed-{repo_id}-"
    if isinstance(listing, list):
        for item in listing:
            path = str(item.get("path", ""))
            if item.get("type") != "file" or not path.startswith(prefix) or path in active_refs:
                continue
            quoted = urllib.parse.quote(path, safe="/")
            gh.json(
                "DELETE",
                f"/repos/{CENTRAL_REPOSITORY}/contents/{quoted}",
                {"message": f"Remove legacy absorbed workflow for {repo['full_name']}", "sha": item["sha"], "branch": "main"},
            )
            deleted_legacy.append(path)

    return [*removed_registry_sources, *deleted_legacy]


def sync_repository(gh: GitHub, full_name: str, worker_url: str, dry_run: bool = False) -> dict:
    repo = gh.repo(full_name)
    policy = _load_policy(gh, int(repo["id"]))
    _preflight_catalog(gh, repo, policy)
    policy_cleanup = _apply_disabled_workflows(gh, repo, policy, dry_run)
    result = core.sync_repository(gh, full_name, worker_url, dry_run)
    result["policy_cleanup"] = policy_cleanup
    if not dry_run:
        result["garbage_collected"] = _finalize_registry_and_gc(gh, repo, policy)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind target workflows to the shared HereLiesAz/workflows catalog.")
    parser.add_argument("--repository", required=True, help="owner/repository")
    parser.add_argument("--worker-url", default=os.environ.get("WORKER_URL", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    result = sync_repository(gh, args.repository, args.worker_url, args.dry_run)
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

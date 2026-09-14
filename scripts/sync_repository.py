#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse

try:
    from . import sync_repository_catalog as core
    from .sync_repository_catalog import *  # noqa: F401,F403
except ImportError:
    import sync_repository_catalog as core
    from sync_repository_catalog import *  # noqa: F401,F403


_base_compile_central = core.compile_central
_base_build_proxy = core.build_proxy


def _rewrite_expression_string(text: str) -> str:
    # Rewrite standalone workflow inputs/vars, but leave github.event.inputs.* and
    # github.event.vars.* intact until github.event itself is translated below.
    # Otherwise github.event.inputs.foo becomes the syntactically invalid
    # fromJSON(inputs.target_event_json).fromJSON(inputs.target_inputs_json).foo.
    text = re.sub(
        r"(?<![A-Za-z0-9_.-])inputs\.([A-Za-z_][A-Za-z0-9_-]*)",
        r"fromJSON(inputs.target_inputs_json).\1",
        text,
    )
    text = re.sub(
        r"(?<![A-Za-z0-9_.-])vars\.([A-Za-z_][A-Za-z0-9_-]*)",
        r"fromJSON(inputs.target_vars_json).\1",
        text,
    )
    for old, new in sorted(core.CONTEXT_REPLACEMENTS, key=lambda pair: len(pair[0]), reverse=True):
        text = text.replace(old, new)
    if "github.event" in text:
        text = text.replace("github.event.", "fromJSON(inputs.target_event_json).")
        text = text.replace("github.event", "fromJSON(inputs.target_event_json)")
    return text


# rewrite_recursive/rewrite_run_string resolve this global at runtime.
core.rewrite_expression_string = _rewrite_expression_string


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


def _proxy_doc(proxy: str) -> tuple[str, dict]:
    lines = proxy.splitlines(keepends=True)
    split_at = 0
    while split_at < len(lines) and (lines[split_at].startswith("#") or not lines[split_at].strip()):
        split_at += 1
    header = "".join(lines[:split_at])
    doc = load_yaml("".join(lines[split_at:]))
    if not isinstance(doc, dict):
        raise ValueError("generated proxy is not a workflow mapping")
    return header, doc


def _compact_event_script(source_path: str) -> str | None:
    if source_path == ".github/workflows/jules-glee.yml":
        jq_filter = r'''{
  action,
  number,
  pull_request: {
    number: .pull_request.number,
    title: (.pull_request.title // ""),
    body: (.pull_request.body // ""),
    base: {ref: .pull_request.base.ref, sha: .pull_request.base.sha},
    head: {
      ref: .pull_request.head.ref,
      sha: .pull_request.head.sha,
      repo: {
        full_name: .pull_request.head.repo.full_name,
        fork: (.pull_request.head.repo.fork // false)
      }
    }
  }
}'''
    elif source_path == ".github/workflows/jules-dispatch.yml":
        jq_filter = r'''{
  action,
  number,
  pull_request: (if .pull_request then {
    number: .pull_request.number,
    title: (.pull_request.title // ""),
    body: (.pull_request.body // ""),
    base: {ref: .pull_request.base.ref, sha: .pull_request.base.sha},
    head: {
      ref: .pull_request.head.ref,
      sha: .pull_request.head.sha,
      repo: {
        full_name: .pull_request.head.repo.full_name,
        fork: (.pull_request.head.repo.fork // false)
      }
    }
  } else null end),
  issue: (if .issue then {
    number: .issue.number,
    title: (.issue.title // ""),
    body: (.issue.body // ""),
    pull_request: (if .issue.pull_request then {url: (.issue.pull_request.url // "")} else null end)
  } else null end),
  comment: (if .comment then {
    body: (.comment.body // ""),
    author_association: (.comment.author_association // ""),
    user: {type: (.comment.user.type // ""), login: (.comment.user.login // "")}
  } else null end),
  review: (if .review then {
    body: (.review.body // ""),
    author_association: (.review.author_association // ""),
    user: {type: (.review.user.type // ""), login: (.review.user.login // "")}
  } else null end)
}'''
    else:
        return None

    return f'''DISPATCH_EVENT_JSON="$(jq -c '{jq_filter}' <<<"$EVENT_JSON")"
'''


def build_proxy(source_text: str, source_path: str, source_hash: str, workflow_name: str) -> str:
    proxy = _base_build_proxy(source_text, source_path, source_hash, workflow_name)
    compact_script = _compact_event_script(source_path)
    needs_jules_gate = source_path == ".github/workflows/jules-dispatch.yml"
    if compact_script is None and not needs_jules_gate:
        return proxy

    header, doc = _proxy_doc(proxy)
    jobs = doc.get("jobs") or {}
    job = jobs.get("central-dispatch")
    if not isinstance(job, dict):
        raise ValueError("generated proxy is missing central-dispatch")

    if needs_jules_gate:
        job["if"] = "${{ github.event_name == 'issues' || github.event_name == 'pull_request' || (github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '@jules')) || (github.event_name == 'pull_request_review_comment' && startsWith(github.event.comment.body, '@jules')) || (github.event_name == 'pull_request_review' && startsWith(github.event.review.body, '@jules')) }}"

    if compact_script is not None:
        steps = job.get("steps") or []
        if not steps or not isinstance(steps[0], dict) or not isinstance(steps[0].get("run"), str):
            raise ValueError("generated proxy dispatch step shape changed")
        run = steps[0]["run"]
        needle = 'payload="$(jq -n'
        if needle not in run or '--argjson event "$EVENT_JSON"' not in run:
            raise ValueError("generated proxy payload shape changed; cannot compact event")
        run = run.replace(needle, compact_script + needle, 1)
        run = run.replace('--argjson event "$EVENT_JSON"', '--argjson event "$DISPATCH_EVENT_JSON"', 1)
        steps[0]["run"] = run

    return header + dump_yaml(doc)


# The core synchronizer resolves these globals at runtime, so patching them here
# makes generated shared workflows use PAT-compatible statuses, curated payload
# minimization, the same Jules event gate as the live catalog, and safe event
# expression rewriting.
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
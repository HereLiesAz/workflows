#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
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

try:
    from .prune_shared_workflow_library import prune_shared_workflow_library
except ImportError:
    from prune_shared_workflow_library import prune_shared_workflow_library


_base_compile_central = core.compile_central
_base_build_proxy = core.build_proxy
_base_sync_repository = core.sync_repository


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

    # Preserve workflow-level permissions on the original jobs. The base
    # centralizer deliberately gives the central workflow a read-only default,
    # but source jobs that inherited e.g. `contents: write` must not be silently
    # downgraded when moved into the shared library.
    source_doc = load_yaml(source_text)
    source_jobs = source_doc.get("jobs") if isinstance(source_doc, dict) else {}
    source_permissions = source_doc.get("permissions") if isinstance(source_doc, dict) else None
    if source_permissions is not None and isinstance(source_jobs, dict):
        for source_job_id, source_job in source_jobs.items():
            compiled_job = jobs.get(source_job_id)
            if (
                isinstance(source_job, dict)
                and isinstance(compiled_job, dict)
                and "permissions" not in source_job
            ):
                compiled_job["permissions"] = core.rewrite_recursive(copy.deepcopy(source_permissions))

    def central_expression(body: str) -> str:
        return "${" + "{ " + body + " }}"

    # Repo-aware actions cannot be allowed to default to the controller repo.
    # softprops/action-gh-release supports explicit repository/token inputs; use
    # the target repository plus the central GH_TOKEN. If the source relied on
    # the action's implicit tag context, reconstruct that context from the proxy
    # inputs and fail clearly for a non-tag dispatch instead of publishing the
    # wrong release.
    for compiled_job in jobs.values():
        if not isinstance(compiled_job, dict):
            continue
        steps = compiled_job.get("steps") or []
        rewritten_steps = []
        for step in steps:
            if (
                isinstance(step, dict)
                and str(step.get("uses") or "").startswith("softprops/action-gh-release@")
            ):
                with_values = step.get("with")
                if with_values is None:
                    with_values = {}
                if not isinstance(with_values, dict):
                    raise ValueError("softprops/action-gh-release has non-mapping with: configuration")
                with_values["repository"] = central_expression("inputs.target_repository")
                with_values["token"] = central_expression("secrets.GH_TOKEN")
                if "tag_name" not in with_values:
                    rewritten_steps.append({
                        "name": "Validate target release ref",
                        "if": central_expression("inputs.target_ref_type != 'tag'"),
                        "shell": "bash",
                        "run": 'echo "softprops/action-gh-release requires a target tag ref; got ${TARGET_REF}" >&2; exit 1',
                    })
                    with_values["tag_name"] = central_expression("inputs.target_ref_name")
                step["with"] = with_values
            rewritten_steps.append(step)
        compiled_job["steps"] = rewritten_steps

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


def _source_uses_event_payload(source_text: str) -> bool:
    # github.event_name is a scalar context and does not require the full event.
    # Any real github.event access, or GITHUB_EVENT_PATH, means source behavior
    # depends on fields we cannot safely discard.
    return (
        re.search(r"(?<![A-Za-z0-9_])github\.event(?:\.|\b)", source_text) is not None
        or "GITHUB_EVENT_PATH" in source_text
    )


def _minimal_pr_event_script() -> str:
    # Generic centralized jobs only need enough PR identity to preserve target
    # status selection and the fork-origin safety guard. GitHub's full PR event
    # embeds large repository/user objects and can exceed the gateway limit.
    return r'''if [[ "$GITHUB_EVENT_NAME" == "pull_request" || "$GITHUB_EVENT_NAME" == "pull_request_target" ]]; then
  DISPATCH_EVENT_JSON="$(jq -c '{
    action,
    number,
    pull_request: {
      number: .pull_request.number,
      base: {
        ref: .pull_request.base.ref,
        sha: .pull_request.base.sha
      },
      head: {
        ref: .pull_request.head.ref,
        sha: .pull_request.head.sha,
        repo: {
          full_name: .pull_request.head.repo.full_name,
          fork: (.pull_request.head.repo.fork // false)
        }
      }
    }
  }' <<<"$EVENT_JSON")"
else
  DISPATCH_EVENT_JSON="$EVENT_JSON"
fi
'''


def _compact_event_script(source_path: str, source_text: str) -> str | None:
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
        if _source_uses_event_payload(source_text):
            return None
        return _minimal_pr_event_script()

    return f'''DISPATCH_EVENT_JSON="$(jq -c '{jq_filter}' <<<"$EVENT_JSON")"
'''


def build_proxy(source_text: str, source_path: str, source_hash: str, workflow_name: str) -> str:
    proxy = _base_build_proxy(source_text, source_path, source_hash, workflow_name)
    compact_script = _compact_event_script(source_path, source_text)
    needs_jules_gate = source_path == ".github/workflows/jules-dispatch.yml"
    if compact_script is None and not needs_jules_gate:
        return proxy

    header, doc = _proxy_doc(proxy)
    jobs = doc.get("jobs") or {}
    job = jobs.get("central-dispatch")
    if not isinstance(job, dict):
        raise ValueError("generated proxy is missing central-dispatch")

    if needs_jules_gate:
        on_value = doc.get("on")
        if isinstance(on_value, dict):
            on_value.pop("pull_request", None)
        job["if"] = "${{ github.event_name == 'issues' || (github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '@jules')) || (github.event_name == 'pull_request_review_comment' && startsWith(github.event.comment.body, '@jules')) || (github.event_name == 'pull_request_review' && startsWith(github.event.review.body, '@jules')) }}"

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
# minimization, explicit-only Jules PR review dispatch, and safe event expression
# rewriting.
def sync_repository(gh, repository: str, worker_url: str, dry_run: bool):
    result = _base_sync_repository(gh, repository, worker_url, dry_run)
    if not dry_run:
        result["shared_library_gc"] = prune_shared_workflow_library(gh, dry_run=False)
    return result


core.compile_central = compile_central
core.build_proxy = build_proxy
core.sync_repository = sync_repository


def main() -> int:
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
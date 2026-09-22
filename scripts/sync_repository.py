#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
import urllib.parse

try:
    from . import sync_repository_catalog as core
    from .sync_repository_catalog import *  # noqa: F401,F403
except ImportError:
    import sync_repository_catalog as core
    from sync_repository_catalog import *  # noqa: F401,F403

try:
    from .repository_workflow_mode import activate as activate_repository_mode
    from .repository_workflow_mode import finalize_manifest
except ImportError:
    from repository_workflow_mode import activate as activate_repository_mode
    from repository_workflow_mode import finalize_manifest

try:
    from .version_contract import (
        Version,
        parse_state,
        render_properties,
        state_payload,
        version_from_properties,
        version_from_text,
    )
except ImportError:
    from version_contract import (
        Version,
        parse_state,
        render_properties,
        state_payload,
        version_from_properties,
        version_from_text,
    )


_base_compile_central = core.compile_central
_base_build_proxy = core.build_proxy
_base_sync_repository = core.sync_repository

TARGET_RUN_TRACKERS = {
    ("hereliesaz/guillotine", ".github/workflows/release-aab.yml"),
}
TRACKER_MARKER = "# central-run-tracker: HereLiesAz/workflows\n"


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


COMPILE_SIGNATURE_RE = re.compile(
    r"(?i)(?:"
    r"(?:^|[\\s;&|])(?:\\./)?gradlew(?:\\.bat)?\\b|"
    r"\\bgradle\\s+[^\\n]*(?:assemble|bundle|build|compile|package)|"
    r"\\b(?:npm|pnpm|yarn)\\s+(?:run\\s+)?build\\b|"
    r"\\bflutter\\s+build\\b|"
    r"\\bcargo\\s+build\\b|"
    r"\\bmvn(?:w)?\\s+[^\\n]*(?:package|install|compile)\\b|"
    r"\\bdotnet\\s+(?:build|publish)\\b|"
    r"\\bcmake\\s+--build\\b|"
    r"\\bmake(?:\\s|$)|"
    r"\\bpyinstaller\\b|"
    r"\\bjpackage\\b"
    r")"
)


def _job_compiles(job: dict) -> bool:
    for value in core.walk_strings(job):
        if isinstance(value, str) and COMPILE_SIGNATURE_RE.search(value):
            return True
    return False


def _merge_needs(needs, dependency: str):
    if needs is None:
        return dependency
    if isinstance(needs, str):
        values = [needs]
    elif isinstance(needs, list):
        values = list(needs)
    else:
        return needs
    values = [value for value in values if value != "central_check_start"]
    if dependency not in values:
        values.append(dependency)
    return values[0] if len(values) == 1 else values


def _resolved_version_step() -> dict:
    return {
        "name": "Apply resolved major.minor.patch.build",
        "shell": "bash",
        "env": {
            "V_MAJOR": "${{ needs.version_contract.outputs.major }}",
            "V_MINOR": "${{ needs.version_contract.outputs.minor }}",
            "V_PATCH": "${{ needs.version_contract.outputs.patch }}",
            "V_BUILD": "${{ needs.version_contract.outputs.build }}",
        },
        "run": r'''set -euo pipefail
python - <<'PY'
from pathlib import Path

path = Path("version.properties")
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
values = {
    "versionMajor": __import__("os").environ["V_MAJOR"],
    "versionMinor": __import__("os").environ["V_MINOR"],
    "versionPatch": __import__("os").environ["V_PATCH"],
    "versionBuild": __import__("os").environ["V_BUILD"],
}
aliases = {
    "MAJOR": values["versionMajor"], "VERSION_MAJOR": values["versionMajor"],
    "MINOR": values["versionMinor"], "VERSION_MINOR": values["versionMinor"],
    "PATCH": values["versionPatch"], "VERSION_PATCH": values["versionPatch"],
    "BUILD": values["versionBuild"], "BUILD_NUMBER": values["versionBuild"], "VERSION_BUILD": values["versionBuild"],
}
seen = set()
out = []
for line in lines:
    stripped = line.strip()
    if "=" not in stripped or stripped.startswith("#"):
        out.append(line)
        continue
    key = stripped.split("=", 1)[0].strip()
    if key in values:
        out.append(f"{key}={values[key]}")
        seen.add(key)
    elif key in aliases:
        out.append(f"{key}={aliases[key]}")
    else:
        out.append(line)
prefix = [f"{key}={values[key]}" for key in values if key not in seen]
if prefix and out and out[0].strip():
    prefix.append("")
path.write_text("\n".join(prefix + out).rstrip() + "\n", encoding="utf-8")
PY
''',
    }


def _version_contract_job() -> dict:
    return {
        "needs": "central_check_start",
        "runs-on": "ubuntu-latest",
        "outputs": {
            "version": "${{ steps.version.outputs.version }}",
            "major": "${{ steps.version.outputs.major }}",
            "minor": "${{ steps.version.outputs.minor }}",
            "patch": "${{ steps.version.outputs.patch }}",
            "build": "${{ steps.version.outputs.build }}",
            "android_version_code": "${{ steps.version.outputs.android_version_code }}",
        },
        "steps": [
            {
                "name": "Checkout source revision",
                "uses": "actions/checkout@v4",
                "with": {
                    "repository": "${{ inputs.target_repository }}",
                    "ref": "${{ inputs.target_sha }}",
                    "fetch-depth": 0,
                    "token": "${{ secrets.GH_TOKEN }}",
                    "persist-credentials": False,
                },
            },
            {
                "name": "Advance canonical version",
                "id": "version",
                "uses": "HereLiesAz/workflows/.github/actions/version-contract@main",
                "with": {
                    "target_repository": "${{ inputs.target_repository }}",
                    "target_sha": "${{ inputs.target_sha }}",
                    "target_ref_name": "${{ inputs.target_ref_name }}",
                    "target_ref_type": "${{ inputs.target_ref_type }}",
                    "token": "${{ secrets.GH_TOKEN }}",
                },
            },
        ],
    }


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
    # downgraded when moved into the central executor.
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

    # Repo-aware release actions must target the source repository, never the
    # controller repository.
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

    compiling_job_ids = [
        job_id
        for job_id, compiled_job in jobs.items()
        if job_id not in {"central_check_start", "central_check_finish"}
        and isinstance(compiled_job, dict)
        and _job_compiles(compiled_job)
    ]
    if compiling_job_ids:
        jobs["version_contract"] = _version_contract_job()
        for job_id in compiling_job_ids:
            compiled_job = jobs[job_id]
            compiled_job["needs"] = _merge_needs(compiled_job.get("needs"), "version_contract")
            job_env = compiled_job.setdefault("env", {})
            if isinstance(job_env, dict):
                job_env.update({
                    "VERSION": "${{ needs.version_contract.outputs.version }}",
                    "VERSION_MAJOR": "${{ needs.version_contract.outputs.major }}",
                    "VERSION_MINOR": "${{ needs.version_contract.outputs.minor }}",
                    "VERSION_PATCH": "${{ needs.version_contract.outputs.patch }}",
                    "VERSION_BUILD": "${{ needs.version_contract.outputs.build }}",
                    "ANDROID_VERSION_CODE": "${{ needs.version_contract.outputs.android_version_code }}",
                })
            steps = compiled_job.get("steps") or []
            if isinstance(steps, list):
                insert_at = 0
                for index, step in enumerate(steps):
                    if isinstance(step, dict) and str(step.get("uses") or "").startswith("actions/checkout@"):
                        insert_at = index + 1
                steps.insert(insert_at, _resolved_version_step())
                compiled_job["steps"] = steps

    start = jobs.get("central_check_start")
    finish = jobs.get("central_check_finish")
    if not isinstance(start, dict) or not isinstance(finish, dict):
        raise ValueError("compiled workflow is missing central reporting jobs")

    if compiling_job_ids:
        finish["needs"] = _merge_needs(finish.get("needs"), "version_contract")

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
payload="$(jq -n --arg state "pending" --arg context "$STATUS_CONTEXT" --arg description "Running from HereLiesAz/workflows." --arg target_url "$DETAILS_URL" '{state:$state,context:$context,description:$description,target_url:$target_url}')"
if ! output="$(gh api --method POST "repos/${TARGET_REPOSITORY}/statuses/${TARGET_CHECK_SHA}" --input - <<<"$payload" 2>&1)"; then
  echo "::warning::Could not post target status: $output"
fi''',
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
  description="Central workflow failed."
else
  state="success"
  description="Central workflow completed successfully."
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
    return (
        re.search(r"(?<![A-Za-z0-9_])github\.event(?:\.|\b)", source_text) is not None
        or "GITHUB_EVENT_PATH" in source_text
    )


def _minimal_pr_event_script() -> str:
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

    header, doc = _proxy_doc(proxy)
    doc["name"] = workflow_name
    jobs = doc.get("jobs") or {}
    job = jobs.get("central-dispatch")
    if not isinstance(job, dict):
        raise ValueError("generated proxy is missing central-dispatch")
    job["name"] = "Dispatch"

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


def _build_target_run_tracker(proxy: str, source_path: str) -> str:
    """Keep a target-side Actions run visible while execution stays centralized."""

    header, doc = _proxy_doc(proxy)
    if TRACKER_MARKER not in header:
        header += TRACKER_MARKER

    doc["permissions"] = {
        "actions": "read",
        "contents": "read",
        "statuses": "read",
    }
    doc["jobs"] = {
        "central-status": {
            "name": "Track centralized run",
            "runs-on": "ubuntu-latest",
            "timeout-minutes": 180,
            "steps": [
                {
                    "name": "Mirror centralized workflow status",
                    "env": {
                        "GH_TOKEN": "${{ github.token }}",
                        "STATUS_CONTEXT": source_path,
                        "TARGET_SHA": "${{ github.sha }}",
                    },
                    "shell": "bash",
                    "run": r'''set -euo pipefail
created_at="$(gh api "repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" --jq .created_at)"
threshold="$(date -u -d "$created_at - 5 seconds" +%s)"
last_state=""

for attempt in $(seq 1 720); do
  statuses="$(gh api "repos/$GITHUB_REPOSITORY/statuses/$TARGET_SHA?per_page=100")"
  row="$(jq -c     --arg context "$STATUS_CONTEXT"     --argjson threshold "$threshold"     '[.[] | select(.context == $context and ((.updated_at | fromdateiso8601) >= $threshold))][0] // empty'     <<<"$statuses")"

  if [[ -n "$row" ]]; then
    state="$(jq -r '.state' <<<"$row")"
    target_url="$(jq -r '.target_url // empty' <<<"$row")"
    if [[ "$state" != "$last_state" ]]; then
      echo "Central workflow state: $state"
      [[ -z "$target_url" ]] || echo "Central run: $target_url"
      last_state="$state"
    fi
    case "$state" in
      success)
        exit 0
        ;;
      failure|error)
        exit 1
        ;;
    esac
  fi

  sleep 15
done

echo "::error::Timed out waiting for centralized workflow status $STATUS_CONTEXT on $TARGET_SHA" >&2
exit 1
''',
                }
            ],
        }
    }
    return header + dump_yaml(doc)


def _prune_rebound_repository_workflows(
    gh,
    repository: str,
    before_manifest: dict,
    after_manifest: dict,
) -> list[str]:
    """Delete obsolete repo-specific executors after a source is rebound to a curated purpose workflow."""

    before_entries = before_manifest.get("workflows") or {}
    after_entries = after_manifest.get("workflows") or {}
    active_after_paths = {
        str(entry.get("central_workflow") or "")
        for entry in after_entries.values()
        if isinstance(entry, dict) and entry.get("status") == "active" and entry.get("central_workflow")
    }
    repo_name = repository.rsplit("/", 1)[-1]
    repo_slug = re.sub(r"[^a-z0-9]+", "-", repo_name.casefold()).strip("-") or "workflow"
    prefix = f".github/workflows/{repo_slug}-"
    removed: list[str] = []

    for source_path, old_entry in before_entries.items():
        if not isinstance(old_entry, dict) or old_entry.get("binding") != "repository":
            continue
        old_path = str(old_entry.get("central_workflow") or "")
        if not old_path.startswith(prefix) or old_path in active_after_paths:
            continue

        new_entry = after_entries.get(source_path)
        if isinstance(new_entry, dict) and new_entry.get("status") == "active" and str(new_entry.get("central_workflow") or "") == old_path:
            continue

        try:
            text, sha = gh.get_file(core.CENTRAL_REPOSITORY, old_path, ref="main")
        except core.ApiError as exc:
            if "-> 404:" in str(exc):
                continue
            raise

        generated_markers = (
            f"# Generated for {repository}:",
            f"# Repository-scoped central workflow for {repository}:",
        )
        if not text.startswith(generated_markers):
            continue

        endpoint = f"/repos/{core.CENTRAL_REPOSITORY}/contents/{urllib.parse.quote(old_path, safe='/')}"
        gh.json(
            "DELETE",
            endpoint,
            {
                "message": f"Remove superseded {repo_name} workflow executor",
                "sha": sha,
                "branch": "main",
            },
        )
        removed.append(old_path)

    return removed




REPOSITORY_REVIEWED_WORKFLOW_BLOBS = {
    "hereliesaz/hereliesaz.github.io": {
        ".github/workflows/dedup_scan.yml": "dbe5a3f49d07e0404c8e679134286235adbcdb17",
        ".github/workflows/publish_admin_staging.yml": "8b54f6169299ab1964797d8442bb1e3681113424",
    },
    "hereliesaz/conveyance-expressive": {
        ".github/workflows/ci.yml": "68a7427c07a2499950a8647f05e832dadb517e59",
    },
    "hereliesaz/conveyance-liquid": {
        ".github/workflows/ci.yml": "1445c059bfcdffbfd19c8c267c3e02baca34e8bd",
    },
    "hereliesaz/conveyance-bacterium": {
        ".github/workflows/ci.yml": "8b32d6357f4b1c826d7f9bcea208df7ea29b7a86",
    },
}

def _enforce_new_workflow_submission_policy(
    gh,
    repository: str,
    manifest: dict,
) -> None:
    """Block brand-new target-repository workflow implementations.

    Existing registered workflow paths are grandfathered. New capabilities must
    be generalized and submitted to HereLiesAz/workflows before a target repo can
    acquire an executable workflow for them.
    """

    registered = manifest.get("workflows") or {}
    try:
        listing = gh.contents(repository, ".github/workflows")
    except core.ApiError as exc:
        if "-> 404:" in str(exc):
            return
        raise

    if not isinstance(listing, list):
        raise RuntimeError(f"{repository}:.github/workflows is not a directory")

    unsubmitted: list[str] = []
    for item in listing:
        path = str(item.get("path") or "")
        if item.get("type") != "file" or not path.endswith((".yml", ".yaml")):
            continue
        if path in registered:
            continue

        reviewed_blobs = REPOSITORY_REVIEWED_WORKFLOW_BLOBS.get(repository.casefold(), {})
        expected_blob = reviewed_blobs.get(path)
        if expected_blob and str(item.get("sha") or "") == expected_blob:
            continue

        # A newly seen path is allowed when its implementation has already been
        # reviewed and admitted to the central catalog. This prevents an older
        # or missing manifest from misclassifying known shared workflows such as
        # jules-glee.yml or sign-azp.yml as brand-new capabilities.
        if path in core.CATALOG_PATH_OVERRIDES:
            continue
        try:
            source_text, _ = gh.get_file(repository, path)
        except core.ApiError:
            unsubmitted.append(path)
            continue
        # Controller-generated proxies are migration residue, not new target
        # workflow implementations. Let the synchronizer recover their registered
        # source and remove/replace the proxy normally.
        if source_text.startswith(core.PROXY_MARKER):
            continue

        source_hash = core.sha256_text(source_text)
        if core.reviewed_override_for_source(source_hash):
            continue

        unsubmitted.append(path)

    if unsubmitted:
        paths = "\n".join(f"  - {path}" for path in sorted(unsubmitted))
        raise RuntimeError(
            "New workflow policy blocked unsubmitted target-repository workflow(s):\n"
            f"{paths}\n"
            "Submit the capability to HereLiesAz/workflows, generalize it for reuse by "
            "any repository, reuse an existing secret when possible, and explicitly "
            "declare the name and purpose of any genuinely new required secret."
        )


def _commit_staged_target_files(
    gh,
    repository: str,
    branch: str,
    staged: dict[str, tuple[str | None, str]],
) -> dict:
    """Commit all target-repository sync writes as one push.

    The legacy synchronizer writes one file at a time through the Contents API,
    which emits one push event per file. On repositories with push-triggered CI
    or GitHub's automatic dependency submission enabled, a single sync therefore
    explodes into a burst of redundant Actions runs. Build one Git tree/commit
    instead so the target sees at most one controller-generated push.
    """

    pending: dict[str, str | None] = {}
    for path, (content, _message) in staged.items():
        try:
            current, _ = gh.get_file(repository, path, ref=branch)
        except core.ApiError as exc:
            if "-> 404:" not in str(exc):
                raise
            current = None
        if content is None:
            if current is not None:
                pending[path] = None
        elif current != content:
            pending[path] = content

    if not pending:
        return {"changed": False, "paths": []}

    branch_ref = urllib.parse.quote(branch, safe="")
    ref = gh.json("GET", f"/repos/{repository}/git/ref/heads/{branch_ref}")
    if not isinstance(ref, dict) or not isinstance(ref.get("object"), dict):
        raise RuntimeError(f"Could not resolve {repository}:{branch}")
    head_sha = str(ref["object"].get("sha") or "")
    if not head_sha:
        raise RuntimeError(f"Could not resolve head SHA for {repository}:{branch}")

    head_commit = gh.json("GET", f"/repos/{repository}/git/commits/{head_sha}")
    if not isinstance(head_commit, dict) or not isinstance(head_commit.get("tree"), dict):
        raise RuntimeError(f"Could not resolve base tree for {repository}:{head_sha}")
    base_tree = str(head_commit["tree"].get("sha") or "")
    if not base_tree:
        raise RuntimeError(f"Could not resolve base tree SHA for {repository}:{head_sha}")

    tree_entries: list[dict[str, object]] = []
    for path, content in sorted(pending.items()):
        if content is None:
            tree_entries.append(
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": None,
                }
            )
            continue
        blob = gh.json(
            "POST",
            f"/repos/{repository}/git/blobs",
            {"content": content, "encoding": "utf-8"},
        )
        if not isinstance(blob, dict) or not blob.get("sha"):
            raise RuntimeError(f"Could not create blob for {repository}:{path}")
        tree_entries.append(
            {
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": str(blob["sha"]),
            }
        )

    tree = gh.json(
        "POST",
        f"/repos/{repository}/git/trees",
        {"base_tree": base_tree, "tree": tree_entries},
    )
    if not isinstance(tree, dict) or not tree.get("sha"):
        raise RuntimeError(f"Could not create sync tree for {repository}")

    commit = gh.json(
        "POST",
        f"/repos/{repository}/git/commits",
        {
            "message": "Centralize workflow bindings and version state [skip ci]",
            "tree": str(tree["sha"]),
            "parents": [head_sha],
        },
    )
    if not isinstance(commit, dict) or not commit.get("sha"):
        raise RuntimeError(f"Could not create sync commit for {repository}")

    commit_sha = str(commit["sha"])
    gh.json(
        "PATCH",
        f"/repos/{repository}/git/refs/heads/{branch_ref}",
        {"sha": commit_sha, "force": False},
    )
    return {
        "changed": True,
        "commit": commit_sha,
        "paths": sorted(pending),
    }


def _initial_repository_version(gh, repository: str, default_branch: str) -> tuple[Version, str]:
    existing = ""
    try:
        existing, _ = gh.get_file(repository, "version.properties", ref=default_branch)
    except core.ApiError as exc:
        if "-> 404:" not in str(exc):
            raise

    version = version_from_properties(existing) or version_from_text(existing)
    if version is None:
        candidates: list[Version] = []
        try:
            tags = gh.json("GET", f"/repos/{repository}/tags?per_page=100")
            if isinstance(tags, list):
                for item in tags:
                    if not isinstance(item, dict):
                        continue
                    candidate = version_from_text(str(item.get("name") or ""))
                    if candidate is not None:
                        candidates.append(candidate)
        except core.ApiError:
            pass
        version = max(candidates) if candidates else Version(0, 0, 0, 0)
    return version, existing


def _ensure_version_contract(gh, repository: str, default_branch: str, dry_run: bool) -> dict:
    version, existing = _initial_repository_version(gh, repository, default_branch)
    normalized = render_properties(existing, version)

    state_text = ""
    try:
        state_text, _ = gh.get_file(repository, ".version-state.json", ref=default_branch)
    except core.ApiError as exc:
        if "-> 404:" not in str(exc):
            raise

    state_source, state_version = parse_state(state_text)
    if state_version is None:
        head = gh.json("GET", f"/repos/{repository}/commits/{default_branch}")
        state_source = str(head.get("sha") or "") if isinstance(head, dict) else ""
        state_text = state_payload(state_source, version, "sync")
    elif not state_source:
        head = gh.json("GET", f"/repos/{repository}/commits/{default_branch}")
        state_source = str(head.get("sha") or "") if isinstance(head, dict) else ""
        state_text = state_payload(state_source, state_version, "sync")

    if not dry_run:
        gh.put_file(
            repository,
            "version.properties",
            normalized,
            f"Enforce canonical version {version} [skip ci]",
            branch=default_branch,
        )
        gh.put_file(
            repository,
            ".version-state.json",
            state_text,
            f"Initialize version state {version} [skip ci]",
            branch=default_branch,
        )

    return {
        "version": str(version),
        "source_sha": state_source,
        "properties_changed": existing != normalized,
        "state_initialized": state_version is None,
    }


def sync_repository(gh, repository: str, worker_url: str, dry_run: bool):
    # Repository mode is mandatory. The legacy core is retained only as a compiler
    # engine; it is never allowed to publish shared_variant families.
    repo_info = gh.repo(repository)
    if repo_info.get("private"):
        raise RuntimeError(
            f"Refusing to sync {repository}: private repositories are excluded from central sync."
        )
    repository_id = int(repo_info["id"])
    default_branch = str(repo_info["default_branch"])
    before_manifest = copy.deepcopy(core.load_manifest(gh, repository_id))
    _enforce_new_workflow_submission_policy(gh, repository, before_manifest)

    # Stage target-repository writes in memory. The legacy synchronizer uses the
    # Contents API per file, which turns one synchronization into many pushes and
    # therefore many redundant Actions runs. Central-repository writes still flow
    # through immediately; only this target/default-branch pair is batched.
    original_put_file = gh.put_file
    staged_target_files: dict[str, tuple[str | None, str]] = {}

    def stage_target_file(
        full_name: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
    ) -> None:
        effective_branch = branch or default_branch
        if (
            full_name.casefold() == repository.casefold()
            and effective_branch == default_branch
        ):
            # A generated proxy is evidence that the source successfully compiled
            # into the central controller. The target must not retain the proxy:
            # future triggers arrive through the repository webhook instead.
            if path.startswith(".github/workflows/") and content.startswith(core.PROXY_MARKER):
                tracker_key = (repository.casefold(), path)
                if tracker_key in TARGET_RUN_TRACKERS:
                    staged_target_files[path] = (
                        _build_target_run_tracker(content, path),
                        f"Preserve centralized workflow run visibility for {path}",
                    )
                else:
                    staged_target_files[path] = (None, f"Remove centralized workflow {path}")
            else:
                staged_target_files[path] = (content, message)
            return
        original_put_file(full_name, path, content, message, branch=branch)

    gh.put_file = stage_target_file
    try:
        version_contract = _ensure_version_contract(
            gh,
            repository,
            default_branch,
            dry_run=dry_run,
        )

        activate_repository_mode(core, repository)
        result = _base_sync_repository(gh, repository, "", dry_run)
        finalize_manifest(gh, core, int(result["repository_id"]), dry_run=dry_run)
    finally:
        gh.put_file = original_put_file

    target_batch = {"changed": False, "paths": []}
    if not dry_run:
        target_batch = _commit_staged_target_files(
            gh,
            repository,
            default_branch,
            staged_target_files,
        )

    removed: list[str] = []
    if not dry_run:
        after_manifest = core.load_manifest(gh, repository_id)
        removed = _prune_rebound_repository_workflows(
            gh,
            repository,
            before_manifest,
            after_manifest,
        )

    for row in result.get("results") or []:
        if not isinstance(row, dict):
            continue
        row.pop("shared_variant", None)
        if row.get("status") == "shared":
            row["status"] = "repository"
    result.pop("shared_library_gc", None)
    if removed:
        result["repository_workflow_gc"] = removed
    result["version_contract"] = version_contract
    result["target_batch"] = target_batch
    result["trigger_transport"] = "repository-webhook"
    result["proxy_files_written"] = 0
    result["tracking_proxy_files_written"] = sum(
        1
        for content, _message in staged_target_files.values()
        if isinstance(content, str) and TRACKER_MARKER in content
    )
    if not dry_run:
        try:
            gh.json(
                "DELETE",
                f"/repos/{repository}/actions/variables/WORKFLOWS_GATEWAY_URL",
            )
        except core.ApiError as exc:
            message = str(exc)
            if "-> 404:" in message:
                pass
            elif "-> 403:" in message:
                print(
                    f"::warning::Could not delete legacy WORKFLOWS_GATEWAY_URL variable for {repository}: {message}"
                )
            else:
                raise
    return result


core.compile_central = compile_central
core.build_proxy = build_proxy
core.sync_repository = sync_repository


def main() -> int:
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

from ruamel.yaml import YAML

try:
    from .sync_repository import (
        CENTRAL_REPOSITORY,
        GitHub,
        OWNER_ID,
        OWNER_LOGIN,
        ApiError,
        load_manifest,
    )
except ImportError:
    from sync_repository import (
        CENTRAL_REPOSITORY,
        GitHub,
        OWNER_ID,
        OWNER_LOGIN,
        ApiError,
        load_manifest,
    )

try:
    from .semantic_catalog import purpose_profile_for_source, uses_purpose_profile, uses_target_repository_name
except ImportError:
    from semantic_catalog import purpose_profile_for_source, uses_purpose_profile, uses_target_repository_name

try:
    from .test_workflow_policy import validation_errors_for_workflow
except ImportError:
    from test_workflow_policy import validation_errors_for_workflow



ROOT = Path(__file__).resolve().parents[1]
MAX_WORKFLOW_DISPATCH_INPUTS = 25


def declared_dispatch_inputs(workflow_path: str) -> dict[str, object]:
    """Return the exact workflow_dispatch input contract for a central workflow."""
    path = ROOT / workflow_path
    if not path.is_file():
        raise RuntimeError(f"Central workflow file is missing: {workflow_path}")

    doc = YAML(typ="safe").load(path.read_text(encoding="utf-8")) or {}
    on_value = doc.get("on") or {}
    dispatch = on_value.get("workflow_dispatch") if isinstance(on_value, dict) else None
    inputs = (dispatch or {}).get("inputs") if isinstance(dispatch, dict) else None
    if inputs is None:
        return {}
    if not isinstance(inputs, dict):
        raise RuntimeError(f"Central workflow has invalid workflow_dispatch inputs: {workflow_path}")
    if len(inputs) > MAX_WORKFLOW_DISPATCH_INPUTS:
        raise RuntimeError(
            f"Central workflow declares {len(inputs)} workflow_dispatch inputs; "
            f"GitHub allows at most {MAX_WORKFLOW_DISPATCH_INPUTS}: {workflow_path}"
        )
    return inputs


def conform_dispatch_inputs(
    workflow_path: str,
    candidate_inputs: dict[str, str],
) -> dict[str, str]:
    """Send only keys the destination workflow actually declares, and verify required keys."""
    declared = declared_dispatch_inputs(workflow_path)
    allowed = set(declared)
    dropped = sorted(set(candidate_inputs) - allowed)
    if dropped:
        print(
            json.dumps(
                {
                    "status": "dispatch-inputs-filtered",
                    "workflow": workflow_path,
                    "dropped": dropped,
                },
                sort_keys=True,
            )
        )

    filtered = {key: value for key, value in candidate_inputs.items() if key in allowed}
    missing_required = [
        key
        for key, spec in declared.items()
        if isinstance(spec, dict) and spec.get("required") is True and key not in filtered
    ]
    if missing_required:
        raise RuntimeError(
            f"Dispatch is missing required inputs for {workflow_path}: "
            + ", ".join(sorted(missing_required))
        )
    return filtered

def validate_central_workflow_binding(
    repository: str,
    binding: str,
    central_workflow: str,
) -> None:
    """Validate that a registered executor matches its catalog binding mode."""
    if binding == "repository":
        repo_name = repository.rsplit("/", 1)[-1]
        namespace = f".github/workflows/{slug(repo_name)}-"
        if not central_workflow.startswith(namespace):
            raise RuntimeError(
                f"Repository-bound central workflow {central_workflow} is outside its namespace {namespace}"
            )
        return

    if binding == "curated":
        policy_errors = validation_errors_for_workflow(central_workflow)
        if policy_errors:
            raise RuntimeError(
                "Central workflow violates generalized workflow policy and cannot execute:\n"
                + "\n".join(f"  - {item}" for item in policy_errors)
            )
        return

    raise RuntimeError(f"Unknown central workflow binding {binding!r} for {repository}")


def require(value: str, name: str) -> str:
    if value is None or value == "":
        raise RuntimeError(f"Missing required dispatch field: {name}")
    return value


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "workflow"


def _patterns(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _ordered_match(value: str, patterns: list[str]) -> bool:
    positives = [p for p in patterns if p and not p.startswith("!")]
    matched = not positives
    for raw in patterns:
        if not raw:
            continue
        negate = raw.startswith("!")
        pattern = raw[1:] if negate else raw
        if fnmatch.fnmatchcase(value, pattern):
            matched = not negate
    return matched


def _any_match(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(value, p) for p in patterns if p)


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).casefold()
    return "rate limit" in text or "retry-after" in text


def _changed_files(gh: GitHub, repository: str, event_name: str, event: dict) -> list[str] | None:
    if event_name == "push":
        files: set[str] = set()
        for commit in event.get("commits") or []:
            if not isinstance(commit, dict):
                continue
            for key in ("added", "modified", "removed"):
                for path in commit.get(key) or []:
                    files.add(str(path))
        head = event.get("head_commit") or {}
        if isinstance(head, dict):
            for key in ("added", "modified", "removed"):
                for path in head.get(key) or []:
                    files.add(str(path))
        return sorted(files)

    if event_name == "pull_request":
        number = event.get("number") or (event.get("pull_request") or {}).get("number")
        if not number:
            return []
        files: list[str] = []
        page = 1
        try:
            while True:
                batch = gh.json(
                    "GET",
                    f"/repos/{repository}/pulls/{int(number)}/files?per_page=100&page={page}",
                )
                if not isinstance(batch, list):
                    break
                files.extend(str(item.get("filename") or "") for item in batch if item.get("filename"))
                if len(batch) < 100:
                    break
                page += 1
        except ApiError as exc:
            if not _is_rate_limit_error(exc):
                raise
            # Path filters are an optimization, not a reason to lose an event.
            # If GitHub's shared-token quota is exhausted, fail open and run the
            # matching workflow rather than silently skipping it.
            return None
        return sorted(set(files))

    return []

WORKFLOW_SETUP_PATHS = (".github/workflows/", ".github/workflow-request.yml")


def _request_sync_if_setup_changed(central_gh: GitHub, repository: str, default_branch: str, event: dict, changed: list[str] | None) -> dict | None:
    """Re-sync a repository when a push to its default branch changes its workflow setup.

    Anyone who can push to the repository (a person, or an LLM session granted only
    that repository) can then add, change or remove centralized workflows without
    access to this controller. The synchronizer's own commits carry [skip ci] and are
    dropped before this runs, so a sync never triggers itself.
    """
    if str(event.get("ref") or "") != f"refs/heads/{default_branch}":
        return None
    touched = [path for path in (changed or []) if path.startswith(WORKFLOW_SETUP_PATHS[0]) or path == WORKFLOW_SETUP_PATHS[1]]
    if not touched:
        return None
    central_gh.json(
        "POST",
        f"/repos/{CENTRAL_REPOSITORY}/actions/workflows/sync-repository.yml/dispatches",
        {"ref": "main", "inputs": {"repository": repository}},
    )
    return {"status": "sync-requested", "repository": repository, "changed": touched}


def _event_trigger(
    source_doc: dict,
    event_name: str,
    event: dict,
    changed_files: list[str] | None,
) -> str | None:
    on_value = source_doc.get("on")
    if isinstance(on_value, str):
        return event_name if on_value == event_name else None
    if isinstance(on_value, list):
        return event_name if event_name in [str(item) for item in on_value] else None
    if not isinstance(on_value, dict):
        return None

    trigger_name = event_name
    if trigger_name not in on_value and event_name == "pull_request" and "pull_request_target" in on_value:
        trigger_name = "pull_request_target"
    if trigger_name not in on_value:
        return None

    spec = on_value.get(trigger_name)
    if spec is None:
        spec = {}
    if not isinstance(spec, dict):
        return trigger_name

    action = str(event.get("action") or "")
    action_types = _patterns(spec.get("types"))
    if action_types:
        if action not in action_types:
            return None
    elif trigger_name in {"pull_request", "pull_request_target"} and action:
        # GitHub Actions does not run an unqualified pull_request trigger for
        # every webhook activity. Its default activity set is opened,
        # synchronize, and reopened; metadata edits, labels, assignments, etc.
        # must not restart CI unless the source explicitly opted into them.
        if action not in {"opened", "synchronize", "reopened"}:
            return None

    if event_name == "push":
        ref = str(event.get("ref") or "")
        is_tag = ref.startswith("refs/tags/")
        ref_name = ref.replace("refs/heads/", "", 1).replace("refs/tags/", "", 1)
        branches = _patterns(spec.get("branches"))
        branch_ignores = _patterns(spec.get("branches-ignore"))
        tags = _patterns(spec.get("tags"))
        tag_ignores = _patterns(spec.get("tags-ignore"))

        if is_tag:
            if branches and not tags:
                return None
            if tags and not _ordered_match(ref_name, tags):
                return None
            if tag_ignores and _any_match(ref_name, tag_ignores):
                return None
        else:
            if tags and not branches:
                return None
            if branches and not _ordered_match(ref_name, branches):
                return None
            if branch_ignores and _any_match(ref_name, branch_ignores):
                return None

    if event_name == "pull_request":
        base_ref = str(((event.get("pull_request") or {}).get("base") or {}).get("ref") or "")
        branches = _patterns(spec.get("branches"))
        branch_ignores = _patterns(spec.get("branches-ignore"))
        if branches and not _ordered_match(base_ref, branches):
            return None
        if branch_ignores and _any_match(base_ref, branch_ignores):
            return None

    paths = _patterns(spec.get("paths"))
    paths_ignore = _patterns(spec.get("paths-ignore"))
    if paths and changed_files is not None:
        if not changed_files or not any(_ordered_match(path, paths) for path in changed_files):
            return None
    if paths_ignore and changed_files is not None and changed_files and all(_any_match(path, paths_ignore) for path in changed_files):
        return None

    return trigger_name


def _local_manifest(repository_id: str) -> dict:
    path = ROOT / "registry" / repository_id / "manifest.json"
    if not path.is_file():
        raise RuntimeError(f"Registry manifest is missing: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Registry manifest is invalid: {path.relative_to(ROOT)}")
    return payload


def _source_document(entry: dict) -> tuple[str, dict]:
    registry_source = str(entry.get("registry_source") or "")
    if not registry_source:
        raise RuntimeError("Registered workflow has no registry_source")
    path = (ROOT / registry_source).resolve()
    if ROOT not in path.parents or not path.is_file():
        raise RuntimeError(f"Registered workflow source is missing: {registry_source}")
    source_text = path.read_text(encoding="utf-8")
    doc = YAML(typ="safe").load(source_text) or {}
    if not isinstance(doc, dict):
        raise RuntimeError(f"Registered workflow source is invalid YAML: {registry_source}")
    return source_text, doc


def _source_uses_repository_vars(source_text: str) -> bool:
    return "vars." in source_text

def _repository_vars(gh: GitHub, repository: str) -> dict[str, str]:
    try:
        data = gh.json("GET", f"/repos/{repository}/actions/variables?per_page=100")
    except ApiError:
        return {}
    variables = data.get("variables") if isinstance(data, dict) else None
    if not isinstance(variables, list):
        return {}
    return {
        str(item.get("name")): str(item.get("value") or "")
        for item in variables
        if item.get("name")
    }


def _dispatch_entry(
    central_gh: GitHub,
    request: dict,
    repository: str,
    repository_id: str,
    source_path: str,
    entry: dict,
    effective_event_name: str,
) -> dict:
    event = request.get("event") or {}
    source_sha256 = require(str(entry.get("source_sha256") or ""), "source_sha256")

    if source_path == ".github/workflows/jules-glee.yml":
        pull_request = event.get("pull_request") or {}
        pr_number = pull_request.get("number") or event.get("number")
        if effective_event_name != "pull_request_target" or event.get("action") != "opened" or not pr_number:
            return {
                "status": "ignored",
                "reason": "Glee only audits an existing pull request when it is opened",
                "source_workflow": source_path,
            }

    if source_path == ".github/workflows/jules-dispatch.yml" and effective_event_name == "pull_request":
        return {
            "status": "ignored",
            "reason": "automatic pull-request auditing belongs to the comment-only Glee workflow",
            "source_workflow": source_path,
        }

    if effective_event_name in {"pull_request", "pull_request_target"}:
        head_repo = (((event.get("pull_request") or {}).get("head") or {}).get("repo") or {})
        if head_repo.get("fork") is True:
            return {
                "status": "ignored",
                "reason": "fork pull requests cannot enter the central secret-bearing executor",
                "source_workflow": source_path,
            }

    central_workflow = require(str(entry.get("central_workflow", "")), "central_workflow")
    binding = str(entry.get("binding") or "")
    validate_central_workflow_binding(
        repository=repository,
        binding=binding,
        central_workflow=central_workflow,
    )

    workflow_id = urllib.parse.quote(central_workflow.rsplit("/", 1)[-1], safe="")
    actor = str(request.get("actor") or "github")
    run_id = str(request.get("run_id") or request.get("webhook_delivery") or f"webhook-{int(time.time())}")
    workflow_name = str(entry.get("name") or source_path)
    workflow_ref = str(request.get("workflow_ref") or f"{repository}/{source_path}@{request.get('sha', '')}")

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
        "target_actor": actor,
        "target_actor_id": str(request.get("actor_id", "")),
        "target_event_name": effective_event_name,
        "target_event_json": json.dumps(event, separators=(",", ":")),
        "target_inputs_json": json.dumps(request.get("inputs") or {}, separators=(",", ":")),
        "target_vars_json": json.dumps(request.get("vars") or {}, separators=(",", ":")),
        "target_run_id": run_id,
        "target_run_number": str(request.get("run_number", "")),
        "target_run_attempt": str(request.get("run_attempt", "1")),
        "target_workflow_ref": workflow_ref,
        "target_workflow_name": workflow_name,
        "source_workflow_path": source_path,
        "source_sha256": source_sha256,
    }

    if uses_target_repository_name(central_workflow):
        dispatch_inputs["target_repository_name"] = repository.rsplit("/", 1)[-1]

    if uses_purpose_profile(central_workflow):
        dispatch_inputs["purpose_profile_json"] = json.dumps(
            purpose_profile_for_source(source_sha256) or {},
            separators=(",", ":"),
        )

    dispatch_inputs = conform_dispatch_inputs(central_workflow, dispatch_inputs)
    body = {"ref": "main", "inputs": dispatch_inputs}
    endpoint = f"/repos/{CENTRAL_REPOSITORY}/actions/workflows/{workflow_id}/dispatches"
    last_error: Exception | None = None
    for delay in (0, 1, 2, 4):
        if delay:
            time.sleep(delay)
        try:
            response = central_gh.json("POST", endpoint, body)
            return {
                "status": "dispatched",
                "repository": repository,
                "source_workflow": source_path,
                "central_workflow": central_workflow,
                "dispatch_response": response,
            }
        except ApiError as exc:
            last_error = exc
            if "-> 404:" not in str(exc):
                raise
    raise RuntimeError(f"Central workflow did not become dispatchable: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a verified repository event to centralized workflows.")
    parser.add_argument("--request", required=True, help="JSON request file")
    args = parser.parse_args()

    with open(args.request, "r", encoding="utf-8") as handle:
        request = json.load(handle)

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    central_gh = GitHub(os.environ.get("CENTRAL_GITHUB_TOKEN") or os.environ.get("GH_TOKEN", ""))
    repository = require(str(request.get("repository", "")), "repository")
    repository_id = require(str(request.get("repository_id", "")), "repository_id")
    event_name = require(str(request.get("event_name", "")), "event_name")
    event = request.get("event") or {}

    # Match GitHub Actions' intentional skip semantics for controller-generated
    # maintenance commits. The webhook transport sees every push, including the
    # controller's own version/proxy-migration commits, so suppress them here
    # before they can fan out into normal application CI.
    if event_name == "push":
        head_commit = event.get("head_commit") or {}
        head_message = str(head_commit.get("message") or "")
        commit_messages = [
            str(item.get("message") or "")
            for item in (event.get("commits") or [])
            if isinstance(item, dict)
        ]
        skip_tokens = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]")
        if any(token in head_message.casefold() for token in skip_tokens) or (
            commit_messages
            and all(any(token in message.casefold() for token in skip_tokens) for message in commit_messages)
        ):
            print(
                json.dumps(
                    {
                        "status": "ignored",
                        "repository": repository,
                        "event_name": event_name,
                        "reason": "push contains an explicit CI-skip token",
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

    # The Worker has already verified webhook ownership and immutable repository
    # identity. Cross-check that signed identity against the registry in this
    # checked-out controller instead of spending shared PAT quota re-fetching it.
    manifest = _local_manifest(repository_id)
    manifest_repo = manifest.get("repository") or {}
    if str(manifest_repo.get("id")) != repository_id:
        raise RuntimeError("Registry repository ID mismatch")
    if str(manifest_repo.get("full_name", "")).casefold() != repository.casefold():
        raise RuntimeError("Registry repository name mismatch")
    if str(manifest_repo.get("owner_id")) != str(OWNER_ID):
        raise RuntimeError("Registry owner ID mismatch")
    if str(manifest_repo.get("owner_login", "")).casefold() != OWNER_LOGIN.casefold():
        raise RuntimeError("Registry owner login mismatch")

    workflows = manifest.get("workflows") or {}
    requested_source = str(request.get("source_workflow_path") or "")
    dispatches: list[dict] = []

    if requested_source:
        entry = workflows.get(requested_source)
        if not entry:
            raise RuntimeError(f"Workflow is not registered: {requested_source}")
        if entry.get("status") != "active":
            raise RuntimeError(f"Workflow is not active: {requested_source} ({entry.get('status')})")
        supplied_hash = str(request.get("source_sha256") or "")
        if supplied_hash and entry.get("source_sha256") != supplied_hash:
            raise RuntimeError("Source hash does not match the central registry")
        source_text, _ = _source_document(entry)
        if not request.get("vars") and _source_uses_repository_vars(source_text):
            request["vars"] = _repository_vars(gh, repository)
        dispatches.append(
            _dispatch_entry(
                central_gh,
                request,
                repository,
                repository_id,
                requested_source,
                entry,
                event_name,
            )
        )
    else:
        changed_files = _changed_files(gh, repository, event_name, event)
        if event_name == "push":
            sync_request = _request_sync_if_setup_changed(
                central_gh,
                repository,
                str(manifest_repo.get("default_branch") or "main"),
                event,
                changed_files,
            )
            if sync_request:
                dispatches.append(sync_request)
        for source_path, entry in sorted(workflows.items()):
            if not isinstance(entry, dict) or entry.get("status") != "active":
                continue
            source_text, source_doc = _source_document(entry)
            effective_event = _event_trigger(source_doc, event_name, event, changed_files)
            if not effective_event:
                continue
            if not request.get("vars") and _source_uses_repository_vars(source_text):
                request["vars"] = _repository_vars(gh, repository)
            dispatches.append(
                _dispatch_entry(
                    central_gh,
                    request,
                    repository,
                    repository_id,
                    source_path,
                    entry,
                    effective_event,
                )
            )

    print(
        json.dumps(
            {
                "status": "routed",
                "repository": repository,
                "event_name": event_name,
                "dispatch_count": sum(1 for item in dispatches if item.get("status") == "dispatched"),
                "results": dispatches,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

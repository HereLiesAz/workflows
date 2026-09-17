#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
from pathlib import PurePosixPath
from typing import Any, Callable

from ruamel.yaml.comments import CommentedMap

_STATE: dict[str, str] = {}
_ORIGINALS: dict[str, Callable[..., Any]] = {}


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return value or "workflow"


def _dedicated_path(repository: str, source_path: str) -> str:
    repo_name = repository.split("/", 1)[-1]
    return f".github/workflows/{_slug(repo_name)}-{_slug(PurePosixPath(source_path).stem)}.yml"


def _contains_secret_reference(value: Any) -> bool:
    if isinstance(value, str):
        return "secrets." in value or "github.token" in value
    if isinstance(value, dict):
        return any(_contains_secret_reference(k) or _contains_secret_reference(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_secret_reference(item) for item in value)
    return False


def _scope_concurrency(value: Any, repo_name: str) -> Any:
    if isinstance(value, str):
        if repo_name in value:
            return value
        return value + f"-{repo_name}"
    if isinstance(value, dict):
        out = CommentedMap(copy.deepcopy(value))
        if "group" in out:
            out["group"] = _scope_concurrency(out["group"], repo_name)
        return out
    return copy.deepcopy(value)


def _job_pushes_git(job: dict[str, Any]) -> bool:
    """Return true when a job shells out to git push.

    Central execution checks out target repositories with credentials disabled by
    default. That is the safest setting for read-only builds, but it breaks source
    workflows whose intended behavior includes pushing tags, version bumps, or
    generated commits back to their own repository.
    """

    for step in job.get("steps") or []:
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if isinstance(run, str) and re.search(r"(?m)(?:^|[\s;&|()])git\s+push(?:\s|$)", run):
            return True
    return False


def _enable_target_git_push_credentials(job: dict[str, Any]) -> None:
    """Persist the central GH_TOKEN only for target checkouts in git-push jobs."""

    if not _job_pushes_git(job):
        return

    for step in job.get("steps") or []:
        if not isinstance(step, dict):
            continue
        uses = str(step.get("uses") or "")
        if not uses.startswith("actions/checkout@"):
            continue

        with_map = step.get("with")
        if with_map is None:
            with_map = CommentedMap()
            step["with"] = with_map
        if not isinstance(with_map, dict):
            continue

        repository_value = str(with_map.get("repository", "")).strip()
        checkout_path = str(with_map.get("path", "")).strip()
        if repository_value not in ("", "${{ inputs.target_repository }}"):
            continue
        if checkout_path not in ("", "."):
            continue

        with_map["repository"] = "${{ inputs.target_repository }}"
        with_map["ref"] = "${{ inputs.target_sha }}"
        with_map["token"] = "${{ secrets.GH_TOKEN }}"
        with_map["persist-credentials"] = True


def activate(core: Any, repository: str) -> None:
    """Switch the legacy synchronizer to clean, one-repository-per-workflow output.

    The old core still contains the shared-family implementation for backward
    compatibility and migration tooling. These runtime hooks deliberately change
    its public output: no shared_variant input, no hash-prefixed jobs, and no
    cross-repository concurrency namespace.
    """

    _STATE.clear()
    _STATE["repository"] = repository

    if not _ORIGINALS:
        _ORIGINALS["semantic_family_slug"] = core.semantic_family_slug
        _ORIGINALS["shared_workflow_path"] = core.shared_workflow_path
        _ORIGINALS["add_shared_variant"] = core.add_shared_variant

    def semantic_family_slug(workflow_name: str, source_path: str, compiled_text: str) -> str:
        _STATE["workflow_name"] = workflow_name
        _STATE["source_path"] = source_path
        return _ORIGINALS["semantic_family_slug"](workflow_name, source_path, compiled_text)

    def shared_workflow_path(workflow_name: str, source_path: str, compiled_text: str) -> str:
        _STATE["workflow_name"] = workflow_name
        _STATE["source_path"] = source_path
        return _dedicated_path(repository, source_path)

    def add_shared_variant(
        existing_text: str | None,
        family_slug: str,
        variant: str,
        compiled_text: str,
    ) -> str:
        del existing_text, family_slug, variant
        doc = core.load_yaml(compiled_text)
        if not isinstance(doc, dict):
            raise ValueError("compiled repository workflow is not a mapping")

        repo_name = repository.split("/", 1)[-1]
        workflow_name = _STATE.get("workflow_name") or "Workflow"
        source_path = _STATE.get("source_path") or ".github/workflows/workflow.yml"

        doc["name"] = f"{repo_name} · {workflow_name}"
        doc["run-name"] = f"{repo_name} · {workflow_name}"

        on_value = doc.get("on") or {}
        dispatch = on_value.get("workflow_dispatch") if isinstance(on_value, dict) else None
        if isinstance(dispatch, dict) and isinstance(dispatch.get("inputs"), dict):
            dispatch["inputs"].pop("shared_variant", None)

        if doc.get("concurrency") is not None:
            doc["concurrency"] = _scope_concurrency(doc["concurrency"], repo_name)

        jobs = doc.get("jobs") or {}
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            if job.get("concurrency") is not None:
                job["concurrency"] = _scope_concurrency(job["concurrency"], repo_name)

            # Read-only jobs keep checkout credentials disabled. Jobs whose source
            # behavior explicitly includes `git push` get an authenticated target
            # checkout so tag/version/release pushes work from the central runner.
            _enable_target_git_push_credentials(job)

            if (
                str(job_id) not in {"central_check_start", "central_check_finish"}
                and "environment" not in job
                and _contains_secret_reference(job)
            ):
                job["environment"] = repo_name

        return (
            f"# Generated for {repository}:{source_path}.\n"
            "# Edit the registered source or synchronizer, not this compiled workflow.\n"
            + core.dump_yaml(doc)
        )

    core.semantic_family_slug = semantic_family_slug
    core.shared_workflow_path = shared_workflow_path
    core.add_shared_variant = add_shared_variant


def finalize_manifest(gh: Any, core: Any, repository_id: int, *, dry_run: bool = False) -> None:
    if dry_run:
        return
    path = core.manifest_path(repository_id)
    text, _ = gh.get_file(core.CENTRAL_REPOSITORY, path, ref="main")
    manifest = json.loads(text)
    changed = False

    repository = str((manifest.get("repository") or {}).get("full_name") or _STATE.get("repository") or "")
    repo_slug = _slug(repository.split("/", 1)[-1]) if repository else ""

    for entry in (manifest.get("workflows") or {}).values():
        if not isinstance(entry, dict) or entry.get("status") != "active":
            continue
        central = str(entry.get("central_workflow") or "")
        if not central.startswith(f".github/workflows/{repo_slug}-"):
            continue
        if entry.get("binding") != "repository" or "shared_variant" in entry:
            entry["binding"] = "repository"
            entry.pop("shared_variant", None)
            changed = True

    if changed:
        gh.put_file(
            core.CENTRAL_REPOSITORY,
            path,
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            f"Use repository-scoped workflows for {repository}",
            branch="main",
        )

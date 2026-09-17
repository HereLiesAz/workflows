#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
from io import StringIO
from pathlib import PurePosixPath
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 4096
_yaml.indent(mapping=2, sequence=4, offset=2)


def load_yaml(text: str) -> Any:
    return _yaml.load(text)


def dump_yaml(data: Any) -> str:
    out = StringIO()
    _yaml.dump(data, out)
    return out.getvalue()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "workflow"


def repository_name(repository_full_name: str) -> str:
    return repository_full_name.rsplit("/", 1)[-1]


def repository_workflow_path(repository_full_name: str, source_path: str) -> str:
    repo = slugify(repository_name(repository_full_name))
    workflow = slugify(PurePosixPath(source_path).stem)
    return f".github/workflows/{repo}-{workflow}.yml"


def _human_job_name(job_id: str) -> str:
    special = {
        "central_check_start": "Start",
        "central_check_finish": "Finish",
    }
    if job_id in special:
        return special[job_id]
    words = re.sub(r"[_-]+", " ", job_id).strip()
    return words[:1].upper() + words[1:] if words else "Job"


def _scope_concurrency(value: Any, repo_slug: str) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if value.casefold().startswith(repo_slug.casefold() + "-"):
            return value
        return f"{repo_slug}-{value}"
    if isinstance(value, dict):
        scoped = CommentedMap(copy.deepcopy(value))
        group = scoped.get("group")
        if group is not None:
            group_text = str(group)
            if not group_text.casefold().startswith(repo_slug.casefold() + "-"):
                scoped["group"] = f"{repo_slug}-{group_text}"
        return scoped
    return copy.deepcopy(value)


def build_repository_workflow(
    repository_full_name: str,
    source_path: str,
    workflow_name: str,
    compiled_text: str,
) -> str:
    """Build one central workflow for one source workflow in one repository.

    Implementation hashes never appear in the generated workflow. They remain
    registry metadata only. Repository identity scopes both the public name and
    concurrency, so unrelated repositories cannot cancel each other's jobs.
    """
    doc = load_yaml(compiled_text)
    if not isinstance(doc, dict):
        raise ValueError("compiled repository workflow is not a mapping")

    jobs = doc.get("jobs") or {}
    if not isinstance(jobs, dict) or not jobs:
        raise ValueError("compiled repository workflow has no jobs")

    repo_name = repository_name(repository_full_name)
    repo_slug = slugify(repo_name)

    on_value = doc.get("on") or {}
    if not isinstance(on_value, dict) or "workflow_dispatch" not in on_value:
        raise ValueError("compiled repository workflow must be workflow_dispatch based")
    dispatch = on_value.get("workflow_dispatch") or {}
    if isinstance(dispatch, dict):
        inputs = dispatch.get("inputs") or {}
        if isinstance(inputs, dict):
            inputs.pop("shared_variant", None)

    if "concurrency" in doc:
        doc["concurrency"] = _scope_concurrency(doc.get("concurrency"), repo_slug)

    cleaned_jobs = CommentedMap()
    for raw_job_id, raw_job in jobs.items():
        job_id = str(raw_job_id)
        if re.match(r"^v_[0-9a-f]{16}__", job_id):
            raise ValueError(f"hash-prefixed job id is forbidden: {job_id}")
        if not isinstance(raw_job, dict):
            raise ValueError(f"job {job_id!r} is not a mapping")

        job = copy.deepcopy(raw_job)
        if "concurrency" in job:
            job["concurrency"] = _scope_concurrency(job.get("concurrency"), repo_slug)

        display_name = str(job.get("name") or _human_job_name(job_id)).strip()
        if not display_name.casefold().startswith(repo_name.casefold() + " ·"):
            job["name"] = f"{repo_name} · {display_name}"
        cleaned_jobs[job_id] = job

    doc["name"] = f"{repo_name} · {workflow_name}"
    doc["run-name"] = f"{repo_name} · {workflow_name}"
    doc["jobs"] = cleaned_jobs

    header = (
        f"# Repository-scoped central workflow for {repository_full_name}.\n"
        "# Implementation hashes are registry metadata only and must never appear here.\n"
    )
    return header + dump_yaml(doc)

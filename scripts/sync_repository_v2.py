#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import re
from typing import Any

from ruamel.yaml.comments import CommentedMap, CommentedSeq

try:
    from . import sync_repository as core
except ImportError:
    import sync_repository as core


CORE_MIGRATION_BLOCKERS = core.migration_blockers
CURRENT_REPOSITORY = ""
CURRENT_REF = ""
LOCAL_REUSABLE_RE = re.compile(r"^\./(.+\.ya?ml)$", re.IGNORECASE)
NEEDS_REF_RE = re.compile(r"\bneeds\.([A-Za-z_][A-Za-z0-9_-]*)\.")
LOCAL_SCRIPT_RE = re.compile(
    r"(?m)(?:^|[\s;&|()])(?:\./)?(?:scripts|\.github/scripts)/[A-Za-z0-9_.@%+,:/=-]+"
)


def _checkout_supports_workspace(step: dict[str, Any]) -> bool:
    uses = step.get("uses")
    if not isinstance(uses, str) or not uses.startswith("actions/checkout@"):
        return False
    with_map = step.get("with") or {}
    if not isinstance(with_map, dict):
        return False
    path = str(with_map.get("path", "")).strip()
    if path not in ("", "."):
        return False
    if with_map.get("sparse-checkout") not in (None, ""):
        return False
    repository = str(with_map.get("repository", "")).strip()
    if repository and repository not in (
        "${{ github.repository }}",
        "${{ inputs.target_repository }}",
        CURRENT_REPOSITORY,
    ):
        return False
    return True


def _local_dependency_blockers(doc: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        target_checkout_seen = False
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            if _checkout_supports_workspace(step):
                target_checkout_seen = True
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith("./") and not target_checkout_seen:
                blockers.append(
                    f"job {job_id!r} step {index} uses local action {uses!r} before a full target-repository checkout"
                )
            run = step.get("run")
            if isinstance(run, str) and LOCAL_SCRIPT_RE.search(run) and not target_checkout_seen:
                blockers.append(
                    f"job {job_id!r} step {index} uses a repo-local scripts/ path before a full target-repository checkout"
                )
    return blockers


def migration_blockers(doc: dict[str, Any]) -> list[str]:
    blockers = CORE_MIGRATION_BLOCKERS(doc)
    blockers.extend(_local_dependency_blockers(doc))
    return sorted(set(blockers))


def _replace_alias_refs(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, str):
        text = value
        for old, new in aliases.items():
            text = re.sub(rf"\bneeds\.{re.escape(old)}\.", f"needs.{new}.", text)
        return text
    if isinstance(value, dict):
        out = CommentedMap()
        for key, item in value.items():
            if key == "needs":
                needs = core._need_list(item)
                rewritten: list[str] = []
                for dependency in needs:
                    rewritten.append(aliases.get(dependency, dependency))
                rewritten = list(dict.fromkeys(rewritten))
                if not rewritten:
                    continue
                out[key] = rewritten[0] if len(rewritten) == 1 else CommentedSeq(rewritten)
            else:
                out[key] = _replace_alias_refs(item, aliases)
        return out
    if isinstance(value, list):
        return CommentedSeq(_replace_alias_refs(item, aliases) for item in value)
    return value


def _resolve_reusable(
    gh: core.GitHub,
    uses: str,
    repository: str,
    ref: str,
) -> tuple[str, str, str, str]:
    local = LOCAL_REUSABLE_RE.match(uses)
    if local:
        reusable_path = local.group(1)
        if not reusable_path.startswith(".github/workflows/"):
            raise ValueError(f"local reusable workflow path is not under .github/workflows: {uses!r}")
        reusable_text, _ = gh.get_file(repository, reusable_path, ref=ref)
        return reusable_text, repository, reusable_path, ref

    owned = core.REUSABLE_RE.match(uses)
    if not owned:
        raise ValueError(f"calls non-owned reusable workflow {uses!r}")
    repo_name, reusable_path, reusable_ref = owned.groups()
    if not reusable_path.startswith(".github/workflows/"):
        raise ValueError(f"reusable workflow path is not under .github/workflows: {uses!r}")
    reusable_repository = f"{core.OWNER_LOGIN}/{repo_name}"
    reusable_text, _ = gh.get_file(reusable_repository, reusable_path, ref=reusable_ref)
    return reusable_text, reusable_repository, reusable_path, reusable_ref


def expand_owned_reusable_workflows(
    gh: core.GitHub,
    doc: dict[str, Any],
    depth: int = 0,
    repository: str | None = None,
    ref: str | None = None,
) -> dict[str, Any]:
    if depth > 4:
        raise ValueError("reusable workflow nesting exceeds four levels")

    repository = repository or CURRENT_REPOSITORY
    ref = ref or CURRENT_REF
    if not repository or not ref:
        raise ValueError("target repository context is required to resolve local reusable workflows")

    expanded = copy.deepcopy(doc)
    jobs = expanded.get("jobs") or {}
    if not isinstance(jobs, dict):
        return expanded

    depended_on: set[str] = set()
    for job in jobs.values():
        if isinstance(job, dict):
            depended_on.update(core._need_list(job.get("needs")))

    new_jobs = CommentedMap()
    aliases: dict[str, str] = {}

    for caller_id, caller in jobs.items():
        if not isinstance(caller, dict) or not isinstance(caller.get("uses"), str):
            new_jobs[caller_id] = copy.deepcopy(caller)
            continue

        uses = caller["uses"]
        try:
            reusable_text, reusable_repository, reusable_path, reusable_ref = _resolve_reusable(
                gh, uses, repository, ref
            )
        except ValueError as exc:
            raise ValueError(f"job {caller_id!r} {exc}") from exc

        reusable = core.load_yaml(reusable_text)
        if not isinstance(reusable, dict):
            raise ValueError(f"job {caller_id!r} reusable workflow {uses!r} is invalid YAML")
        on_value = reusable.get("on")
        call = on_value.get("workflow_call") if isinstance(on_value, dict) else None
        if not isinstance(on_value, dict) or "workflow_call" not in on_value:
            raise ValueError(f"{uses!r} is not a workflow_call workflow")
        if isinstance(call, dict) and call.get("outputs"):
            raise ValueError(f"{uses!r} declares workflow_call outputs")

        reusable = expand_owned_reusable_workflows(
            gh,
            reusable,
            depth + 1,
            repository=reusable_repository,
            ref=reusable_ref,
        )
        inner_jobs = reusable.get("jobs") or {}
        if not isinstance(inner_jobs, dict) or not inner_jobs:
            raise ValueError(f"{uses!r} has no jobs")
        if caller_id in depended_on and len(inner_jobs) != 1:
            raise ValueError(
                f"job {caller_id!r} is depended on downstream and expands to {len(inner_jobs)} jobs; only single-job dependency aliasing is supported"
            )

        call_inputs = call.get("inputs", {}) if isinstance(call, dict) else {}
        caller_inputs = caller.get("with", {}) or {}
        input_values: dict[str, Any] = {}
        for name, spec in call_inputs.items():
            if name in caller_inputs:
                input_values[name] = caller_inputs[name]
            elif isinstance(spec, dict) and "default" in spec:
                input_values[name] = spec["default"]
            elif isinstance(spec, dict) and spec.get("required"):
                raise ValueError(f"job {caller_id!r} does not provide required reusable input {name!r}")
            else:
                input_values[name] = ""

        call_secrets = call.get("secrets", {}) if isinstance(call, dict) else {}
        caller_secrets = caller.get("secrets") or {}
        secret_values: dict[str, Any] = {}
        if caller_secrets == "inherit":
            for name in call_secrets:
                secret_values[name] = "${{ secrets." + str(name) + " }}"
        elif isinstance(caller_secrets, dict):
            for name, spec in call_secrets.items():
                if name in caller_secrets:
                    secret_values[name] = caller_secrets[name]
                elif isinstance(spec, dict) and spec.get("required"):
                    raise ValueError(f"job {caller_id!r} does not provide required reusable secret {name!r}")
                else:
                    secret_values[name] = ""
        else:
            raise ValueError(f"job {caller_id!r} has unsupported secrets configuration")

        caller_if = caller.get("if")
        caller_needs = core._need_list(caller.get("needs"))
        reusable_env = reusable.get("env") if isinstance(reusable.get("env"), dict) else {}
        reusable_concurrency = reusable.get("concurrency")
        generated_ids: list[str] = []

        for inner_id, inner_job in inner_jobs.items():
            if not isinstance(inner_job, dict):
                raise ValueError(f"{uses!r} contains invalid job {inner_id!r}")
            generated_id = f"{caller_id}__{inner_id}"
            if generated_id in new_jobs or generated_id in jobs:
                raise ValueError(f"inlined reusable workflow job id collision: {generated_id!r}")
            generated_ids.append(generated_id)
            inlined = core._replace_reusable_context(copy.deepcopy(inner_job), input_values, secret_values)
            if caller_if is not None:
                inlined["if"] = core.add_condition(inlined.get("if"), str(caller_if))
            core._rewrite_needs_for_inline(inlined, caller_id, caller_needs)
            if reusable_env:
                merged_env = CommentedMap(copy.deepcopy(reusable_env))
                if isinstance(inlined.get("env"), dict):
                    merged_env.update(inlined["env"])
                inlined["env"] = merged_env
            if reusable_concurrency is not None and len(inner_jobs) == 1 and "concurrency" not in inlined:
                inlined["concurrency"] = copy.deepcopy(reusable_concurrency)
            new_jobs[generated_id] = inlined

        if len(generated_ids) == 1:
            aliases[caller_id] = generated_ids[0]

    if aliases:
        new_jobs = _replace_alias_refs(new_jobs, aliases)

    expanded["jobs"] = new_jobs
    return expanded


def sync_repository(
    gh: core.GitHub,
    full_name: str,
    worker_url: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    global CURRENT_REPOSITORY, CURRENT_REF
    repo = gh.repo(full_name)
    previous_repository, previous_ref = CURRENT_REPOSITORY, CURRENT_REF
    CURRENT_REPOSITORY = repo["full_name"]
    CURRENT_REF = repo["default_branch"]
    try:
        return core.sync_repository(gh, full_name, worker_url, dry_run)
    finally:
        CURRENT_REPOSITORY, CURRENT_REF = previous_repository, previous_ref


def main() -> int:
    parser = argparse.ArgumentParser(description="Absorb target-repository workflows into HereLiesAz/workflows.")
    parser.add_argument("--repository", required=True, help="owner/repository")
    parser.add_argument("--worker-url", default=os.environ.get("WORKER_URL", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    core.expand_owned_reusable_workflows = expand_owned_reusable_workflows
    core.migration_blockers = migration_blockers

    gh = core.GitHub(os.environ.get("GH_TOKEN", ""))
    result = sync_repository(gh, args.repository, args.worker_url, args.dry_run)
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

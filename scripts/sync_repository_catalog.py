#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import socket
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

try:
    from .shared_workflow_library import add_shared_variant, semantic_family_slug, shared_workflow_path
except ImportError:
    from shared_workflow_library import add_shared_variant, semantic_family_slug, shared_workflow_path

try:
    from .semantic_catalog import reviewed_override_for_source
except ImportError:
    from semantic_catalog import reviewed_override_for_source

API_VERSION = "2026-03-10"
PROXY_MARKER = "# centralized-by: HereLiesAz/workflows"
OWNER_LOGIN = "HereLiesAz"
OWNER_ID = 103241502
CENTRAL_REPOSITORY = "HereLiesAz/workflows"
WORKER_AUDIENCE = "hereliesaz-workflows"
WORKER_VARIABLE = "WORKFLOWS_GATEWAY_URL"

# Curated, target-aware shared workflows. These are real reusable implementations,
# not per-repository compiled copies.
CATALOG_PATH_OVERRIDES = {
    ".github/workflows/jules-dispatch.yml": ".github/workflows/jules-dispatch.yml",
    ".github/workflows/jules-glee.yml": ".github/workflows/jules-glee.yml",
    ".github/workflows/backup.yml": ".github/workflows/context-backup.yml",
    ".github/workflows/clear_cache.yml": ".github/workflows/clear-cache.yml",
}

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)


class ApiError(RuntimeError):
    pass


def _rate_limit_delay(headers: dict[str, str], attempt: int) -> int | None:
    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    if retry_after:
        try:
            return max(1, min(int(retry_after), 120))
        except ValueError:
            pass
    remaining = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
    reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
    if remaining == "0" and reset:
        try:
            import time
            return max(1, min(int(reset) - int(time.time()) + 1, 120))
        except ValueError:
            pass
    return min(2 ** attempt, 30)


class GitHub:
    def __init__(self, token: str):
        if not token:
            raise RuntimeError("GH_TOKEN is required")
        self.token = token

    def request(self, method: str, path: str, body: Any | None = None) -> tuple[int, dict[str, str], bytes]:
        import time
        url = path if path.startswith("https://") else f"https://api.github.com{path}"
        data = None if body is None else json.dumps(body).encode()
        for attempt in range(4):
            req = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.token}",
                    "X-GitHub-Api-Version": API_VERSION,
                    "User-Agent": "HereLiesAz-workflows-centralizer",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.status, dict(response.headers), response.read()
            except urllib.error.HTTPError as exc:
                payload = exc.read().decode(errors="replace")
                headers = dict(exc.headers)
                rate_limited = exc.code in (403, 429) and (
                    "rate limit" in payload.casefold()
                    or headers.get("Retry-After")
                    or headers.get("X-RateLimit-Remaining") == "0"
                )
                if not rate_limited or attempt >= 3:
                    raise ApiError(f"{method} {url} -> {exc.code}: {payload}") from exc
                time.sleep(_rate_limit_delay(headers, attempt) or 1)
            except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                if attempt >= 3:
                    raise ApiError(f"{method} {url} -> network timeout/error: {exc}") from exc
                time.sleep(min(2 ** attempt, 8))
        raise AssertionError("unreachable")

    def json(self, method: str, path: str, body: Any | None = None) -> Any:
        status, _, raw = self.request(method, path, body)
        if status == 204 or not raw:
            return None
        return json.loads(raw)

    def repo(self, full_name: str) -> dict[str, Any]:
        return self.json("GET", f"/repos/{full_name}")

    def contents(self, full_name: str, path: str, ref: str | None = None) -> list[dict[str, Any]] | dict[str, Any]:
        quoted = urllib.parse.quote(path, safe="/")
        endpoint = f"/repos/{full_name}/contents/{quoted}"
        if ref:
            endpoint += "?ref=" + urllib.parse.quote(ref, safe="")
        return self.json("GET", endpoint)

    def get_file(self, full_name: str, path: str, ref: str | None = None) -> tuple[str, str]:
        item = self.contents(full_name, path, ref=ref)
        if not isinstance(item, dict) or item.get("type") != "file":
            raise ApiError(f"{full_name}:{path} is not a file")
        content = base64.b64decode(item["content"]).decode()
        return content, item["sha"]

    def put_file(self, full_name: str, path: str, content: str, message: str, branch: str | None = None) -> None:
        quoted = urllib.parse.quote(path, safe="/")
        existing_sha = None
        try:
            item = self.contents(full_name, path, ref=branch)
            if isinstance(item, dict):
                existing_sha = item.get("sha")
                encoded = item.get("content")
                if isinstance(encoded, str):
                    current = base64.b64decode(encoded).decode()
                    if current == content:
                        return
        except ApiError as exc:
            if "-> 404:" not in str(exc):
                raise

        body: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        if existing_sha:
            body["sha"] = existing_sha
        if branch:
            body["branch"] = branch
        self.json("PUT", f"/repos/{full_name}/contents/{quoted}", body)

    def upsert_variable(self, full_name: str, name: str, value: str) -> None:
        quoted = urllib.parse.quote(name, safe="")
        try:
            existing = self.json("GET", f"/repos/{full_name}/actions/variables/{quoted}")
            if isinstance(existing, dict) and existing.get("value") == value:
                return
            self.json("PATCH", f"/repos/{full_name}/actions/variables/{quoted}", {"name": name, "value": value})
        except ApiError as exc:
            if "-> 404:" not in str(exc):
                raise
            self.json("POST", f"/repos/{full_name}/actions/variables", {"name": name, "value": value})


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def slugify(path: str) -> str:
    stem = PurePosixPath(path).stem
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-").lower() or "workflow"
    suffix = hashlib.sha1(path.encode()).hexdigest()[:8]
    return f"{slug}-{suffix}"


def load_yaml(text: str) -> Any:
    return yaml.load(text)


def dump_yaml(data: Any) -> str:
    from io import StringIO
    out = StringIO()
    yaml.dump(data, out)
    return out.getvalue()


def contains_workflow_call(on_value: Any) -> bool:
    return isinstance(on_value, dict) and "workflow_call" in on_value


def workflow_call_only(on_value: Any) -> bool:
    return isinstance(on_value, dict) and set(on_value.keys()) == {"workflow_call"}


def walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from walk_strings(k)
            yield from walk_strings(v)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)


LOCAL_SCRIPT_RE = re.compile(
    r"(?m)(?:^|[\s;&|()])(?:\./)?(?:scripts|\.github/scripts)/[A-Za-z0-9_.@%+,:/=-]+"
)


def _checkout_supports_local_dependencies(step: dict[str, Any]) -> bool:
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
    return repository in ("", "${{ github.repository }}", "${{ inputs.target_repository }}")


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
            if _checkout_supports_local_dependencies(step):
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


def central_execution_blockers(doc: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    unsafe_action_prefixes = (
        "actions/deploy-pages@",
        "actions/labeler@",
        "gradle/actions/dependency-submission@",
        "google-labs-code/jules-invoke@",
        "google-labs-code/jules-action@",
    )
    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        environment = job.get("environment")
        if isinstance(environment, dict) and str(environment.get("name", "")).lower() == "github-pages":
            blockers.append(f"job {job_id!r} deploys to the runner repository's github-pages environment")
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith(unsafe_action_prefixes):
                blockers.append(f"job {job_id!r} step {index} uses repository-bound action {uses!r}")
            if isinstance(uses, str) and uses.startswith("actions/github-script@"):
                script = str((step.get("with") or {}).get("script", ""))
                if any(token in script for token in (
                    "context.repo", "context.issue", "context.eventName", "context.payload"
                )):
                    blockers.append(
                        f"job {job_id!r} step {index} uses actions/github-script with runner-repository context"
                    )
    return blockers


def migration_blockers(doc: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    on_value = doc.get("on")
    if workflow_call_only(on_value):
        blockers.append("workflow_call-only libraries require caller expansion before target removal")

    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        uses = job.get("uses")
        if isinstance(uses, str):
            blockers.append(f"job {job_id!r} still contains an unexpanded reusable workflow call")
        if job.get("secrets") == "inherit":
            blockers.append(f"job {job_id!r} uses secrets: inherit")

    blockers.extend(_local_dependency_blockers(doc))
    blockers.extend(central_execution_blockers(doc))

    strings = "\n".join(walk_strings(doc))
    if "GITHUB_EVENT_PATH" in strings or "github.event_path" in strings:
        blockers.append("workflow reads GITHUB_EVENT_PATH/github.event_path directly")
    if "github.workflow_sha" in strings:
        blockers.append("workflow depends on github.workflow_sha")
    if "github.action_repository" in strings or "github.action_ref" in strings:
        blockers.append("workflow depends on action-execution-specific github context")

    return sorted(set(blockers))


REUSABLE_RE = re.compile(r"^HereLiesAz/([^/]+)/(.+\.ya?ml)@([^@]+)$", re.IGNORECASE)
LOCAL_REUSABLE_RE = re.compile(r"^\./(.+\.ya?ml)$", re.IGNORECASE)


def _need_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _replace_reusable_context(value: Any, input_values: dict[str, Any], secret_values: dict[str, Any]) -> Any:
    if isinstance(value, str):
        text = value
        for key, replacement in input_values.items():
            whole = "${{ inputs." + key + " }}"
            if text.strip() == whole:
                return copy.deepcopy(replacement)
            if isinstance(replacement, str):
                if replacement.startswith("${{") and replacement.endswith("}}"):
                    expr = replacement[3:-2].strip()
                    text = text.replace(f"inputs.{key}", f"({expr})")
                else:
                    text = text.replace(whole, replacement)
        for key, replacement in secret_values.items():
            whole = "${{ secrets." + key + " }}"
            if text.strip() == whole:
                return copy.deepcopy(replacement)
            if isinstance(replacement, str):
                if replacement.startswith("${{") and replacement.endswith("}}"):
                    expr = replacement[3:-2].strip()
                    text = text.replace(f"secrets.{key}", f"({expr})")
                else:
                    text = text.replace(whole, replacement)
        return text
    if isinstance(value, dict):
        out = CommentedMap()
        for key, item in value.items():
            out[key] = _replace_reusable_context(item, input_values, secret_values)
        return out
    if isinstance(value, list):
        return CommentedSeq(_replace_reusable_context(item, input_values, secret_values) for item in value)
    return value


def _rewrite_needs_for_inline(job: dict[str, Any], prefix: str, caller_needs: list[str]) -> None:
    inner = _need_list(job.get("needs"))
    prefixed = [f"{prefix}__{item}" for item in inner]
    combined = [*caller_needs, *prefixed]
    if not combined:
        job.pop("needs", None)
    elif len(combined) == 1:
        job["needs"] = combined[0]
    else:
        job["needs"] = CommentedSeq(dict.fromkeys(combined))


def _replace_dependency_aliases(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, str):
        text = value
        for old, new in aliases.items():
            text = re.sub(rf"\bneeds\.{re.escape(old)}\.", f"needs.{new}.", text)
        return text
    if isinstance(value, dict):
        out = CommentedMap()
        for key, item in value.items():
            if key == "needs":
                needs = _need_list(item)
                rewritten = [aliases.get(dep, dep) for dep in needs]
                rewritten = list(dict.fromkeys(rewritten))
                if not rewritten:
                    continue
                out[key] = rewritten[0] if len(rewritten) == 1 else CommentedSeq(rewritten)
            else:
                out[key] = _replace_dependency_aliases(item, aliases)
        return out
    if isinstance(value, list):
        return CommentedSeq(_replace_dependency_aliases(item, aliases) for item in value)
    return value


def _expression_body(value: Any) -> str:
    text = str(value).strip()
    while text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2].strip()
    return text


def add_condition(existing: Any, extra: str) -> str:
    extra_body = _expression_body(extra)
    if existing is None:
        return "${{ " + extra_body + " }}"
    existing_body = _expression_body(existing)
    return "${{ (" + existing_body + ") && (" + extra_body + ") }}"


def _resolve_reusable_workflow(
    gh: GitHub,
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

    match = REUSABLE_RE.match(uses)
    if not match:
        raise ValueError(f"calls non-owned reusable workflow {uses!r}")
    repo_name, reusable_path, reusable_ref = match.groups()
    if not reusable_path.startswith(".github/workflows/"):
        raise ValueError(f"reusable workflow path is not under .github/workflows: {uses!r}")
    reusable_repository = f"{OWNER_LOGIN}/{repo_name}"
    reusable_text, _ = gh.get_file(reusable_repository, reusable_path, ref=reusable_ref)
    return reusable_text, reusable_repository, reusable_path, reusable_ref


def expand_owned_reusable_workflows(
    gh: GitHub,
    doc: dict[str, Any],
    depth: int = 0,
    repository: str | None = None,
    ref: str | None = None,
) -> dict[str, Any]:
    if depth > 4:
        raise ValueError("reusable workflow nesting exceeds four levels")
    if not repository or not ref:
        raise ValueError("target repository and ref are required to resolve reusable workflows")

    expanded = copy.deepcopy(doc)
    jobs = expanded.get("jobs") or {}
    if not isinstance(jobs, dict):
        return expanded

    depended_on: set[str] = set()
    for job in jobs.values():
        if isinstance(job, dict):
            depended_on.update(_need_list(job.get("needs")))

    new_jobs = CommentedMap()
    aliases: dict[str, str] = {}

    for caller_id, caller in jobs.items():
        if not isinstance(caller, dict) or not isinstance(caller.get("uses"), str):
            new_jobs[caller_id] = copy.deepcopy(caller)
            continue

        uses = caller["uses"]
        try:
            reusable_text, reusable_repository, reusable_path, reusable_ref = _resolve_reusable_workflow(
                gh, uses, repository, ref
            )
        except ValueError as exc:
            raise ValueError(f"job {caller_id!r} {exc}") from exc

        reusable = load_yaml(reusable_text)
        if not isinstance(reusable, dict):
            raise ValueError(f"reusable workflow {uses!r} is invalid YAML")
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
        caller_secrets = caller.get("secrets")
        secret_values: dict[str, Any] = {}
        if caller_secrets == "inherit":
            for name in call_secrets:
                secret_values[name] = "${{ secrets." + str(name) + " }}"
        else:
            caller_secret_map = caller_secrets or {}
            if not isinstance(caller_secret_map, dict):
                raise ValueError(f"job {caller_id!r} has unsupported secrets configuration")
            for name, spec in call_secrets.items():
                if name in caller_secret_map:
                    secret_values[name] = caller_secret_map[name]
                elif isinstance(spec, dict) and spec.get("required"):
                    raise ValueError(f"job {caller_id!r} does not provide required reusable secret {name!r}")
                else:
                    secret_values[name] = ""

        caller_if = caller.get("if")
        caller_needs = _need_list(caller.get("needs"))
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

            inlined = _replace_reusable_context(copy.deepcopy(inner_job), input_values, secret_values)
            if caller_if is not None:
                inlined["if"] = add_condition(inlined.get("if"), str(caller_if))
            _rewrite_needs_for_inline(inlined, caller_id, caller_needs)
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
        new_jobs = _replace_dependency_aliases(new_jobs, aliases)

    expanded["jobs"] = new_jobs
    return expanded


CONTEXT_REPLACEMENTS = [
    ("github.repository_owner_id", "inputs.target_repository_owner_id"),
    ("github.repository_id", "inputs.target_repository_id"),
    ("github.repository_owner", "inputs.target_repository_owner"),
    ("github.repository", "inputs.target_repository"),
    ("github.event_name", "inputs.target_event_name"),
    ("github.head_ref", "inputs.target_head_ref"),
    ("github.base_ref", "inputs.target_base_ref"),
    ("github.ref_name", "inputs.target_ref_name"),
    ("github.ref_type", "inputs.target_ref_type"),
    ("github.ref", "inputs.target_ref"),
    ("github.sha", "inputs.target_sha"),
    ("github.actor_id", "inputs.target_actor_id"),
    ("github.actor", "inputs.target_actor"),
    ("github.triggering_actor", "inputs.target_actor"),
    ("github.run_attempt", "inputs.target_run_attempt"),
    ("github.run_number", "inputs.target_run_number"),
    ("github.run_id", "inputs.target_run_id"),
    ("github.workflow_ref", "inputs.target_workflow_ref"),
    ("github.workflow", "inputs.target_workflow_name"),
    ("github.token", "secrets.GH_TOKEN"),
    ("secrets.GITHUB_TOKEN", "secrets.GH_TOKEN"),
]

RUN_ENV_REPLACEMENTS = [
    ("GITHUB_REPOSITORY_OWNER_ID", "TARGET_REPOSITORY_OWNER_ID"),
    ("GITHUB_REPOSITORY_OWNER", "TARGET_REPOSITORY_OWNER"),
    ("GITHUB_REPOSITORY_ID", "TARGET_REPOSITORY_ID"),
    ("GITHUB_REPOSITORY", "TARGET_REPOSITORY"),
    ("GITHUB_EVENT_NAME", "TARGET_EVENT_NAME"),
    ("GITHUB_HEAD_REF", "TARGET_HEAD_REF"),
    ("GITHUB_BASE_REF", "TARGET_BASE_REF"),
    ("GITHUB_REF_NAME", "TARGET_REF_NAME"),
    ("GITHUB_REF_TYPE", "TARGET_REF_TYPE"),
    ("GITHUB_REF", "TARGET_REF"),
    ("GITHUB_SHA", "TARGET_SHA"),
    ("GITHUB_ACTOR_ID", "TARGET_ACTOR_ID"),
    ("GITHUB_ACTOR", "TARGET_ACTOR"),
    ("GITHUB_RUN_ATTEMPT", "TARGET_RUN_ATTEMPT"),
    ("GITHUB_RUN_NUMBER", "TARGET_RUN_NUMBER"),
    ("GITHUB_RUN_ID", "TARGET_RUN_ID"),
    ("GITHUB_WORKFLOW_REF", "TARGET_WORKFLOW_REF"),
    ("GITHUB_WORKFLOW", "TARGET_WORKFLOW_NAME"),
]


def rewrite_expression_string(text: str) -> str:
    text = re.sub(r"(?<![A-Za-z0-9_.-])inputs\.([A-Za-z_][A-Za-z0-9_-]*)", r"fromJSON(inputs.target_inputs_json).\1", text)
    text = re.sub(r"(?<![A-Za-z0-9_.-])vars\.([A-Za-z_][A-Za-z0-9_-]*)", r"fromJSON(inputs.target_vars_json).\1", text)
    for old, new in sorted(CONTEXT_REPLACEMENTS, key=lambda pair: len(pair[0]), reverse=True):
        text = text.replace(old, new)
    if "github.event" in text:
        text = text.replace("github.event.", "fromJSON(inputs.target_event_json).")
        text = text.replace("github.event", "fromJSON(inputs.target_event_json)")
    return text


def rewrite_run_string(text: str) -> str:
    text = rewrite_expression_string(text)
    for old, new in RUN_ENV_REPLACEMENTS:
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    return text


def rewrite_recursive(value: Any, in_run: bool = False) -> Any:
    if isinstance(value, str):
        return rewrite_run_string(value) if in_run else rewrite_expression_string(value)
    if isinstance(value, dict):
        out = CommentedMap()
        for key, val in value.items():
            out[key] = rewrite_recursive(val, in_run=(key == "run"))
        return out
    if isinstance(value, list):
        return CommentedSeq(rewrite_recursive(item) for item in value)
    return value


def ensure_checkout_target(job: dict[str, Any]) -> None:
    steps = job.get("steps")
    if not isinstance(steps, list):
        return
    for step in steps:
        if not isinstance(step, dict):
            continue
        uses = step.get("uses")
        if not isinstance(uses, str) or not uses.startswith("actions/checkout@"):
            continue
        with_map = step.setdefault("with", CommentedMap())
        if not isinstance(with_map, dict):
            continue
        with_map.setdefault("repository", "${{ inputs.target_repository }}")
        with_map.setdefault("ref", "${{ inputs.target_sha }}")
        with_map.setdefault("token", "${{ secrets.GH_TOKEN }}")
        with_map["persist-credentials"] = False


def job_has_checkout(job: Any) -> bool:
    if not isinstance(job, dict) or not isinstance(job.get("steps"), list):
        return False
    return any(
        isinstance(step, dict)
        and isinstance(step.get("uses"), str)
        and step["uses"].startswith("actions/checkout@")
        for step in job["steps"]
    )


def job_uses_secrets(job: Any) -> bool:
    if not isinstance(job, dict):
        return False
    flattened = "\n".join(walk_strings(job))
    return "secrets." in flattened or "github.token" in flattened


def add_need(job: dict[str, Any], dependency: str) -> None:
    current = job.get("needs")
    if current is None:
        job["needs"] = dependency
    elif isinstance(current, str):
        if current != dependency:
            job["needs"] = CommentedSeq([dependency, current])
    elif isinstance(current, list) and dependency not in current:
        job["needs"] = CommentedSeq([dependency, *current])


def compile_central(source_text: str, target: dict[str, Any], source_path: str, check_name: str) -> str:
    source = load_yaml(source_text)
    if not isinstance(source, dict) or not isinstance(source.get("jobs"), dict):
        raise ValueError("workflow must contain a jobs mapping")
    blockers = migration_blockers(source)
    if blockers:
        raise ValueError("; ".join(blockers))

    original_jobs = copy.deepcopy(source["jobs"])
    rewritten_jobs = rewrite_recursive(original_jobs)
    for job_id, job in rewritten_jobs.items():
        if not isinstance(job, dict):
            continue
        add_need(job, "__central_check_start")
        ensure_checkout_target(job)
        if job_uses_secrets(original_jobs.get(job_id)) or job_has_checkout(original_jobs.get(job_id)):
            fork_guard = "inputs.target_event_name != 'pull_request' || fromJSON(inputs.target_event_json).pull_request.head.repo.fork != true"
            job["if"] = add_condition(job.get("if"), fork_guard)

    source_name = source.get("name") or PurePosixPath(source_path).name
    inputs = CommentedMap()
    for name, required in [
        ("target_repository", True), ("target_repository_id", True),
        ("target_repository_owner", True), ("target_repository_owner_id", True),
        ("target_sha", True), ("target_check_sha", True), ("target_ref", True),
        ("target_ref_name", False), ("target_ref_type", False), ("target_head_ref", False),
        ("target_base_ref", False), ("target_actor", True), ("target_actor_id", False),
        ("target_event_name", True), ("target_event_json", True), ("target_inputs_json", True),
        ("target_vars_json", True), ("target_run_id", True), ("target_run_number", False),
        ("target_run_attempt", False), ("target_workflow_ref", False), ("target_workflow_name", True),
        ("source_workflow_path", True), ("source_sha256", True),
    ]:
        inputs[name] = CommentedMap({"required": required, "type": "string"})

    doc = CommentedMap()
    doc["name"] = f"{source_name} [shared catalog]"
    doc["on"] = CommentedMap({"workflow_dispatch": CommentedMap({"inputs": inputs})})
    doc["permissions"] = CommentedMap({"contents": "read"})
    source_env = rewrite_recursive(copy.deepcopy(source.get("env") or {}))
    merged_env = CommentedMap(source_env if isinstance(source_env, dict) else {})
    merged_env.update({
        "TARGET_REPOSITORY": "${{ inputs.target_repository }}",
        "TARGET_REPOSITORY_ID": "${{ inputs.target_repository_id }}",
        "TARGET_REPOSITORY_OWNER": "${{ inputs.target_repository_owner }}",
        "TARGET_REPOSITORY_OWNER_ID": "${{ inputs.target_repository_owner_id }}",
        "TARGET_SHA": "${{ inputs.target_sha }}", "TARGET_CHECK_SHA": "${{ inputs.target_check_sha }}",
        "TARGET_REF": "${{ inputs.target_ref }}", "TARGET_REF_NAME": "${{ inputs.target_ref_name }}",
        "TARGET_REF_TYPE": "${{ inputs.target_ref_type }}", "TARGET_HEAD_REF": "${{ inputs.target_head_ref }}",
        "TARGET_BASE_REF": "${{ inputs.target_base_ref }}", "TARGET_ACTOR": "${{ inputs.target_actor }}",
        "TARGET_ACTOR_ID": "${{ inputs.target_actor_id }}", "TARGET_EVENT_NAME": "${{ inputs.target_event_name }}",
        "TARGET_RUN_ID": "${{ inputs.target_run_id }}", "TARGET_RUN_NUMBER": "${{ inputs.target_run_number }}",
        "TARGET_RUN_ATTEMPT": "${{ inputs.target_run_attempt }}", "TARGET_WORKFLOW_REF": "${{ inputs.target_workflow_ref }}",
        "TARGET_WORKFLOW_NAME": "${{ inputs.target_workflow_name }}",
    })
    doc["env"] = merged_env
    if source.get("defaults") is not None:
        doc["defaults"] = rewrite_recursive(copy.deepcopy(source["defaults"]))
    if source.get("concurrency") is not None:
        doc["concurrency"] = rewrite_recursive(copy.deepcopy(source["concurrency"]))

    jobs = CommentedMap()
    jobs["__central_check_start"] = CommentedMap({
        "runs-on": "ubuntu-latest",
        "outputs": {"check_id": "${{ steps.create.outputs.check_id }}"},
        "steps": [
            {
                "name": "Validate immutable target identity",
                "env": {"GH_TOKEN": "${{ secrets.GH_TOKEN }}"},
                "shell": "bash",
                "run": '''set -euo pipefail
repo_owner="${TARGET_REPOSITORY%%/*}"
[[ -n "$TARGET_REPOSITORY_ID" ]] || { echo "Missing repository ID" >&2; exit 1; }
[[ "${repo_owner,,}" == "hereliesaz" ]] || { echo "Repository owner mismatch" >&2; exit 1; }
[[ "${TARGET_REPOSITORY_OWNER,,}" == "hereliesaz" ]] || { echo "OIDC owner login mismatch" >&2; exit 1; }
[[ "$TARGET_REPOSITORY_OWNER_ID" == "103241502" ]] || { echo "OIDC owner ID mismatch" >&2; exit 1; }''',
            },
            {
                "name": "Create target check", "id": "create",
                "env": {
                    "GH_TOKEN": "${{ secrets.GH_TOKEN }}", "CHECK_NAME": "${{ inputs.target_workflow_name }}",
                    "DETAILS_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
                },
                "shell": "bash",
                "run": '''set -euo pipefail
gh_api_json_with_retry() {
  local method="$1" endpoint="$2" payload="$3"
  local attempt=1 max_attempts=3 delay=5 output rc
  while true; do
    set +e
    output="$(gh api --method "$method" "$endpoint" --input - <<<"$payload" 2>&1)"
    rc=$?
    set -e
    if [[ $rc -eq 0 ]]; then
      printf '%s' "$output"
      return 0
    fi
    if [[ $attempt -ge $max_attempts ]] || ! grep -Eqi 'rate limit|HTTP 403|HTTP 429|secondary rate' <<<"$output"; then
      printf '%s\n' "$output" >&2
      return "$rc"
    fi
    printf 'GitHub API quota unavailable while posting target check; retry %d/%d in %ds.\n' "$attempt" "$max_attempts" "$delay" >&2
    sleep "$delay"
    attempt=$((attempt + 1))
    if [[ $delay -lt 300 ]]; then
      delay=$((delay * 2))
      [[ $delay -le 300 ]] || delay=300
    fi
  done
}
payload="$(jq -n --arg name "$CHECK_NAME" --arg sha "$TARGET_CHECK_SHA" --arg details "$DETAILS_URL" '{name:$name,head_sha:$sha,status:"in_progress",details_url:$details,output:{title:$name,summary:"Running from the shared workflow catalog."}}')"
if response="$(gh_api_json_with_retry POST "repos/${TARGET_REPOSITORY}/check-runs" "$payload")"; then
  echo "check_id=$(jq -r '.id' <<<"$response")" >> "$GITHUB_OUTPUT"
else
  echo "::warning::Could not create target check; continuing without external status reporting."
  echo "check_id=" >> "$GITHUB_OUTPUT"
fi''',
            },
        ],
    })

    for job_id, job in rewritten_jobs.items():
        if job_id.startswith("__central_"):
            raise ValueError(f"job id {job_id!r} uses reserved __central_ prefix")
        jobs[job_id] = job

    original_job_ids = list(rewritten_jobs.keys())
    jobs["__central_check_finish"] = CommentedMap({
        "if": "${{ always() }}",
        "needs": CommentedSeq(["__central_check_start", *original_job_ids]),
        "runs-on": "ubuntu-latest",
        "steps": [{
            "name": "Complete target check",
            "env": {
                "GH_TOKEN": "${{ secrets.GH_TOKEN }}",
                "CHECK_ID": "${{ needs.__central_check_start.outputs.check_id }}",
                "CHECK_NAME": "${{ inputs.target_workflow_name }}",
                "FAILED": "${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}",
                "DETAILS_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
            },
            "shell": "bash",
            "run": '''set -euo pipefail
[[ -n "${CHECK_ID:-}" ]] || exit 0
if [[ "$FAILED" == "true" ]]; then conclusion="failure"; summary="Shared catalog workflow failed. Open the linked run for details."; else conclusion="success"; summary="Shared catalog workflow completed successfully."; fi
gh_api_json_with_retry() {
  local method="$1" endpoint="$2" payload="$3"
  local attempt=1 max_attempts=3 delay=5 output rc
  while true; do
    set +e
    output="$(gh api --method "$method" "$endpoint" --input - <<<"$payload" 2>&1)"
    rc=$?
    set -e
    if [[ $rc -eq 0 ]]; then
      printf '%s' "$output"
      return 0
    fi
    if [[ $attempt -ge $max_attempts ]] || ! grep -Eqi 'rate limit|HTTP 403|HTTP 429|secondary rate' <<<"$output"; then
      printf '%s\n' "$output" >&2
      return "$rc"
    fi
    printf 'GitHub API quota unavailable while posting target check; retry %d/%d in %ds.\n' "$attempt" "$max_attempts" "$delay" >&2
    sleep "$delay"
    attempt=$((attempt + 1))
    if [[ $delay -lt 300 ]]; then
      delay=$((delay * 2))
      [[ $delay -le 300 ]] || delay=300
    fi
  done
}
payload="$(jq -n --arg conclusion "$conclusion" --arg title "$CHECK_NAME" --arg summary "$summary" --arg details "$DETAILS_URL" '{status:"completed",conclusion:$conclusion,details_url:$details,output:{title:$title,summary:$summary}}')"
if ! gh_api_json_with_retry PATCH "repos/${TARGET_REPOSITORY}/check-runs/${CHECK_ID}" "$payload" >/dev/null; then
  echo "::warning::Could not complete target check; workflow result remains authoritative."
fi''',
        }],
    })
    doc["jobs"] = jobs
    return "# Generated shared catalog workflow. Do not edit by hand.\n" + f"# catalog-source: {source_path}\n" + dump_yaml(doc)


def build_proxy(source_text: str, source_path: str, source_hash: str, workflow_name: str) -> str:
    source = load_yaml(source_text)
    on_value = copy.deepcopy(source.get("on"))
    if on_value is None:
        raise ValueError("workflow has no 'on' trigger")

    doc = CommentedMap()
    doc["name"] = f"{workflow_name} [central proxy]"
    doc["on"] = on_value
    doc["permissions"] = CommentedMap({"contents": "read", "id-token": "write"})
    dispatch_script = '''set -euo pipefail
[[ -n "${WORKFLOWS_GATEWAY_URL:-}" ]] || { echo "Repository variable WORKFLOWS_GATEWAY_URL is not configured." >&2; exit 1; }
oidc_response="$(curl --fail-with-body --silent --show-error -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=hereliesaz-workflows")"
oidc_token="$(jq -r '.value // empty' <<<"$oidc_response")"
[[ -n "$oidc_token" ]] || { echo "GitHub did not issue an OIDC token." >&2; exit 1; }
echo "::add-mask::$oidc_token"
payload="$(jq -n \
  --arg repository "$GITHUB_REPOSITORY" --arg repository_id "$GITHUB_REPOSITORY_ID" \
  --arg repository_owner "$GITHUB_REPOSITORY_OWNER" --arg repository_owner_id "$GITHUB_REPOSITORY_OWNER_ID" \
  --arg sha "$GITHUB_SHA" --arg ref "$GITHUB_REF" --arg ref_name "$GITHUB_REF_NAME" --arg ref_type "$GITHUB_REF_TYPE" \
  --arg head_ref "$GITHUB_HEAD_REF" --arg base_ref "$GITHUB_BASE_REF" --arg actor "$GITHUB_ACTOR" --arg actor_id "$GITHUB_ACTOR_ID" \
  --arg event_name "$GITHUB_EVENT_NAME" --arg run_id "$GITHUB_RUN_ID" --arg run_number "$GITHUB_RUN_NUMBER" --arg run_attempt "$GITHUB_RUN_ATTEMPT" \
  --arg workflow_ref "$GITHUB_WORKFLOW_REF" --arg workflow_name "$GITHUB_WORKFLOW" --arg source_workflow_path "$SOURCE_WORKFLOW_PATH" \
  --arg source_sha256 "$SOURCE_SHA256" --argjson event "$EVENT_JSON" --argjson inputs "$INPUTS_JSON" --argjson vars "$VARS_JSON" \
  '{repository:$repository,repository_id:$repository_id,repository_owner:$repository_owner,repository_owner_id:$repository_owner_id,sha:$sha,check_sha:($event.pull_request.head.sha // $sha),ref:$ref,ref_name:$ref_name,ref_type:$ref_type,head_ref:$head_ref,base_ref:$base_ref,actor:$actor,actor_id:$actor_id,event_name:$event_name,event:$event,inputs:$inputs,vars:$vars,run_id:$run_id,run_number:$run_number,run_attempt:$run_attempt,workflow_ref:$workflow_ref,workflow_name:$workflow_name,source_workflow_path:$source_workflow_path,source_sha256:$source_sha256}')"
curl --fail-with-body --silent --show-error -X POST "${WORKFLOWS_GATEWAY_URL%/}/dispatch" -H "Authorization: Bearer ${oidc_token}" -H "Content-Type: application/json" --data-binary "$payload"'''

    doc["jobs"] = CommentedMap({"central-dispatch": CommentedMap({
        "runs-on": "ubuntu-latest",
        "steps": [{
            "name": "Dispatch to HereLiesAz/workflows",
            "env": {
                "WORKFLOWS_GATEWAY_URL": "${{ vars.WORKFLOWS_GATEWAY_URL }}",
                "EVENT_JSON": "${{ toJSON(github.event) }}", "INPUTS_JSON": "${{ toJSON(inputs) }}", "VARS_JSON": "${{ toJSON(vars) }}",
                "SOURCE_WORKFLOW_PATH": source_path, "SOURCE_SHA256": source_hash,
            },
            "shell": "bash", "run": dispatch_script,
        }],
    })})
    return f"{PROXY_MARKER}\n# central-source-path: {source_path}\n# central-source-sha256: {source_hash}\n# This file intentionally contains no repository secrets.\n" + dump_yaml(doc)


def manifest_path(repo_id: int) -> str:
    return f"registry/{repo_id}/manifest.json"


def load_manifest(gh: GitHub, repo_id: int) -> dict[str, Any]:
    path = manifest_path(repo_id)
    try:
        text, _ = gh.get_file(CENTRAL_REPOSITORY, path)
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except ApiError as exc:
        if "-> 404:" not in str(exc):
            raise
    return {"schema": 2, "workflows": {}}


def catalog_hash(doc: dict[str, Any]) -> str:
    implementation = copy.deepcopy(doc)
    implementation.pop("name", None)
    implementation.pop("on", None)
    return sha256_text(dump_yaml(implementation))


def catalog_name_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return slug[:72].rstrip("-") or "workflow"


def catalog_workflow_path(doc: dict[str, Any], workflow_name: str) -> str:
    return f".github/workflows/catalog-{catalog_name_slug(workflow_name)}-{catalog_hash(doc)[:16]}.yml"


def discover_catalog_workflow_paths(gh: GitHub) -> dict[str, str]:
    listing = gh.contents(CENTRAL_REPOSITORY, ".github/workflows", ref="main")
    if not isinstance(listing, list):
        raise RuntimeError("Central .github/workflows is not a directory")

    by_hash: dict[str, str] = {}
    for item in listing:
        if item.get("type") != "file":
            continue
        name = str(item.get("name", ""))
        match = re.fullmatch(r"catalog-(?:.+-)?([0-9a-f]{16})\.ya?ml", name)
        if not match:
            continue
        hash16 = match.group(1)
        path = str(item.get("path", ""))
        current = by_hash.get(hash16)
        if current is None or re.fullmatch(r"\.github/workflows/catalog-[0-9a-f]{16}\.ya?ml", current):
            by_hash[hash16] = path
    return by_hash


def _proxy_original_source(gh: GitHub, manifest_entry: dict[str, Any] | None) -> str | None:
    if not manifest_entry:
        return None
    registry_source = manifest_entry.get("registry_source")
    if not registry_source:
        return None
    try:
        source, _ = gh.get_file(CENTRAL_REPOSITORY, str(registry_source))
        return source
    except ApiError:
        return None


def sync_repository(gh: GitHub, full_name: str, worker_url: str, dry_run: bool = False) -> dict[str, Any]:
    repo = gh.repo(full_name)
    owner = repo["owner"]
    if int(owner["id"]) != OWNER_ID or owner["login"].lower() != OWNER_LOGIN.lower():
        raise RuntimeError(f"Refusing {full_name}: repository is not owned by {OWNER_LOGIN} ({OWNER_ID})")
    if repo.get("private"):
        raise RuntimeError(f"Refusing {full_name}: private repositories are excluded from central sync")
    if repo["full_name"].lower() == CENTRAL_REPOSITORY.lower():
        raise RuntimeError("Refusing to centralize the central workflows repository itself")

    repo_id = int(repo["id"])
    default_branch = repo["default_branch"]
    manifest = load_manifest(gh, repo_id)
    manifest["schema"] = 2
    manifest["repository"] = {"id": repo_id, "full_name": repo["full_name"], "owner_id": int(owner["id"]), "owner_login": owner["login"], "default_branch": default_branch}
    workflows_manifest = manifest.setdefault("workflows", {})

    try:
        listing = gh.contents(repo["full_name"], ".github/workflows")
    except ApiError as exc:
        if "-> 404:" in str(exc):
            listing = []
        else:
            raise
    if not isinstance(listing, list):
        raise RuntimeError(".github/workflows is not a directory")

    results: list[dict[str, Any]] = []
    if worker_url and not dry_run:
        gh.upsert_variable(repo["full_name"], WORKER_VARIABLE, worker_url.rstrip("/"))

    live_paths = {
        item.get("path", "")
        for item in listing
        if item.get("type") == "file" and item.get("path", "").endswith((".yml", ".yaml"))
    }
    # A workflow the target repository deleted stops appearing in `listing`, so the loop
    # below never revisits its manifest entry. Left untouched, a stale "active" entry
    # permanently blocks _prune_rebound_repository_workflows from ever recognizing the
    # central compiled duplicate (if any) as unreachable and deleting it. Mark it obsolete
    # here, from the live listing alone, before anything else can rely on its old status.
    for stale_path, stale_entry in workflows_manifest.items():
        if stale_path in live_paths or not isinstance(stale_entry, dict):
            continue
        if stale_entry.get("status") != "active":
            continue
        # The sync itself removes a target's workflow file once its source is registered
        # and bound centrally; that absence is the intended steady state, not a deletion.
        if stale_entry.get("centralized"):
            continue
        stale_entry["status"] = "obsolete"
        stale_entry["reason"] = "workflow file no longer exists in the target repository"
        stale_entry["updated_at"] = now_iso()

    for item in listing:
        path = item.get("path", "")
        if item.get("type") != "file" or not path.endswith((".yml", ".yaml")):
            continue

        visible_text, _ = gh.get_file(repo["full_name"], path)
        prior_state = workflows_manifest.get(path)
        is_proxy = visible_text.startswith(PROXY_MARKER)
        source_text = visible_text
        if is_proxy:
            recovered = _proxy_original_source(gh, prior_state)
            if recovered is None:
                results.append({"path": path, "status": "blocked", "blockers": ["proxy exists but its original registry source cannot be recovered"]})
                continue
            source_text = recovered

        source_hash = sha256_text(source_text)
        parsed = load_yaml(source_text)
        if not isinstance(parsed, dict):
            results.append({"path": path, "status": "blocked", "reason": "invalid workflow YAML"})
            continue
        workflow_name = str(parsed.get("name") or PurePosixPath(path).name)
        slug = slugify(path)
        registry_source = f"registry/{repo_id}/{slug}.source.yml"

        if "glee" in workflow_name.casefold() and path != ".github/workflows/jules-glee.yml":
            blockers = [
                "legacy Glee workflow disabled: Glee may only use the canonical repoless Codex audit and one PR comment"
            ]
            workflows_manifest[path] = {
                "status": "blocked",
                "source_sha256": source_hash,
                "name": workflow_name,
                "blockers": blockers,
                "registry_source": registry_source,
                "updated_at": now_iso(),
            }
            if not dry_run:
                gh.put_file(
                    CENTRAL_REPOSITORY,
                    registry_source,
                    source_text,
                    f"Register disabled legacy Glee workflow {repo['full_name']}:{path}",
                    branch="main",
                )
            results.append({"path": path, "status": "blocked", "blockers": blockers})
            continue

        if workflow_call_only(parsed.get("on")):
            workflows_manifest[path] = {"status": "library", "name": workflow_name, "source_sha256": source_hash, "registry_source": registry_source, "updated_at": now_iso()}
            if not dry_run:
                gh.put_file(CENTRAL_REPOSITORY, registry_source, source_text, f"Register workflow library {repo['full_name']}:{path}", branch="main")
                if is_proxy:
                    gh.put_file(repo["full_name"], path, source_text, f"Restore reusable workflow library {path}", branch=default_branch)
            results.append({"path": path, "status": "library"})
            continue

        override = reviewed_override_for_source(source_hash) or CATALOG_PATH_OVERRIDES.get(path)
        if override:
            try:
                gh.get_file(CENTRAL_REPOSITORY, override)
            except ApiError:
                workflows_manifest[path] = {"status": "blocked", "name": workflow_name, "source_sha256": source_hash, "blockers": [f"catalog override is missing: {override}"], "updated_at": now_iso()}
                results.append({"path": path, "status": "blocked", "blockers": [f"catalog override is missing: {override}"]})
                continue
            workflows_manifest[path] = {"status": "active", "name": workflow_name, "source_sha256": source_hash, "registry_source": registry_source, "central_workflow": override, "binding": "curated", "centralized": True, "updated_at": now_iso()}
            if not dry_run:
                gh.put_file(CENTRAL_REPOSITORY, registry_source, source_text, f"Register {repo['full_name']}:{path}", branch="main")
                proxy = build_proxy(source_text, path, source_hash, workflow_name)
                gh.put_file(repo["full_name"], path, proxy, f"Refresh {path} from shared catalog via {CENTRAL_REPOSITORY}", branch=default_branch)
            results.append({"path": path, "status": "catalog", "central_workflow": override, "source_sha256": source_hash})
            continue

        try:
            expanded = expand_owned_reusable_workflows(gh, parsed, repository=repo["full_name"], ref=default_branch)
            blockers = migration_blockers(expanded)
        except Exception as exc:
            expanded = parsed
            blockers = [str(exc)]

        if blockers:
            workflows_manifest[path] = {"status": "local", "source_sha256": source_hash, "name": workflow_name, "blockers": blockers, "registry_source": registry_source, "updated_at": now_iso()}
            if not dry_run:
                gh.put_file(CENTRAL_REPOSITORY, registry_source, source_text, f"Register local workflow {repo['full_name']}:{path}", branch="main")
                if is_proxy:
                    gh.put_file(repo["full_name"], path, source_text, f"Restore local workflow {path}; central execution is unsafe", branch=default_branch)
            results.append({"path": path, "status": "local", "blockers": blockers})
            continue

        implementation_hash = catalog_hash(expanded)
        shared_variant = implementation_hash[:16]
        try:
            compiled = compile_central(
                dump_yaml(expanded),
                {"full_name": "HereLiesAz/workflows-library", "private": True},
                f"shared/{implementation_hash}",
                workflow_name,
            )
            family_slug = semantic_family_slug(workflow_name, path, compiled)
            central_workflow = shared_workflow_path(workflow_name, path, compiled)
            existing_shared = None
            try:
                existing_shared, _ = gh.get_file(CENTRAL_REPOSITORY, central_workflow, ref="main")
            except ApiError as exc:
                if "-> 404:" not in str(exc):
                    raise
            shared_text = add_shared_variant(
                existing_shared,
                family_slug,
                shared_variant,
                compiled,
            )
            proxy = build_proxy(source_text, path, source_hash, workflow_name)
        except Exception as exc:
            workflows_manifest[path] = {"status": "local", "source_sha256": source_hash, "name": workflow_name, "blockers": [str(exc)], "registry_source": registry_source, "updated_at": now_iso()}
            if not dry_run and is_proxy:
                gh.put_file(repo["full_name"], path, source_text, f"Restore local workflow {path}; shared-library compilation failed", branch=default_branch)
            results.append({"path": path, "status": "local", "blockers": [str(exc)]})
            continue

        workflows_manifest[path] = {
            "status": "active",
            "name": workflow_name,
            "source_sha256": source_hash,
            "registry_source": registry_source,
            "central_workflow": central_workflow,
            "binding": "shared-variant",
            "centralized": True,
            "implementation_sha256": implementation_hash,
            "shared_variant": shared_variant,
            "updated_at": now_iso(),
        }
        if not dry_run:
            gh.put_file(CENTRAL_REPOSITORY, registry_source, source_text, f"Register {repo['full_name']}:{path}", branch="main")
            gh.put_file(CENTRAL_REPOSITORY, central_workflow, shared_text, f"Update shared workflow family {family_slug}", branch="main")
            gh.put_file(repo["full_name"], path, proxy, f"Refresh {path} from shared workflow library via {CENTRAL_REPOSITORY}", branch=default_branch)
        results.append({
            "path": path,
            "status": "shared",
            "central_workflow": central_workflow,
            "implementation_sha256": implementation_hash,
            "shared_variant": shared_variant,
            "source_sha256": source_hash,
        })

    manifest["last_sync_at"] = now_iso()
    manifest["worker_url_configured"] = bool(worker_url)
    if not dry_run:
        gh.put_file(CENTRAL_REPOSITORY, manifest_path(repo_id), json.dumps(manifest, indent=2, sort_keys=True) + "\n", f"Update workflow registry for {repo['full_name']}", branch="main")

    return {"repository": repo["full_name"], "repository_id": repo_id, "default_branch": default_branch, "results": results, "manifest": manifest_path(repo_id)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind target-repository workflows to the shared HereLiesAz/workflows catalog.")
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

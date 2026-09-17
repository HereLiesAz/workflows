#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from ruamel.yaml import YAML

try:
    from .semantic_catalog import GENERAL_CURATED_NAMES, SEMANTIC_WORKFLOWS
except ImportError:
    from semantic_catalog import GENERAL_CURATED_NAMES, SEMANTIC_WORKFLOWS

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REGISTRY = ROOT / "registry"
CURATED = {
    ".github/workflows/jules-dispatch.yml",
    ".github/workflows/jules-glee.yml",
    ".github/workflows/context-backup.yml",
    ".github/workflows/clear-cache.yml",
    ".github/workflows/morphont-publish.yml",
} | set(SEMANTIC_WORKFLOWS)
CONTROLLER = {
    ".github/workflows/gateway.yml",
    ".github/workflows/sync-repository.yml",
    ".github/workflows/sync-all-repositories.yml",
    ".github/workflows/validate-controller.yml",
}
OBSOLETE_RUNTIME = {
    ".github/workflows/emergency-concurrency-fix.yml",
    ".github/workflows/migrate-repository-workflows.yml",
    ".github/workflows/migrate-semantic-library.yml",
    ".github/workflows/repair-release-centralization.yml",
}
GLOBAL_SECRETS = {"GH_TOKEN", "GITHUB_TOKEN"}
HASH_JOB_RE = re.compile(r"^v_[0-9a-f]{16}__")
SECRET_RE = re.compile(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)")
_yaml = YAML(typ="safe")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "workflow"


def expected_repository_workflow(repository: str, source_path: str) -> str:
    repo_name = repository.rsplit("/", 1)[-1]
    return f".github/workflows/{slug(repo_name)}-{slug(PurePosixPath(source_path).stem)}.yml"


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def secret_names(value: Any) -> set[str]:
    out: set[str] = set()
    for text in strings(value):
        out.update(SECRET_RE.findall(text))
        if "github.token" in text:
            out.add("GITHUB_TOKEN")
    return out


def concurrency_groups(doc: dict[str, Any]):
    top = doc.get("concurrency")
    if isinstance(top, str):
        yield "workflow", top
    elif isinstance(top, dict) and top.get("group") is not None:
        yield "workflow", str(top["group"])
    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        value = job.get("concurrency")
        if isinstance(value, str):
            yield str(job_id), value
        elif isinstance(value, dict) and value.get("group") is not None:
            yield str(job_id), str(value["group"])


def audit() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    stats: Counter[str] = Counter()
    workflow_docs: dict[str, dict[str, Any]] = {}
    workflow_text: dict[str, str] = {}

    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        rel = path.relative_to(ROOT).as_posix()
        stats["workflow_files"] += 1
        text = path.read_text(encoding="utf-8")
        workflow_text[rel] = text
        try:
            doc = _yaml.load(text)
        except Exception as exc:
            errors.append(f"{rel}: invalid YAML: {exc}")
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict) or not doc["jobs"]:
            errors.append(f"{rel}: workflow must contain a non-empty jobs mapping")
            continue
        workflow_docs[rel] = doc
        if re.search(r"-[0-9a-f]{16}\.ya?ml$", path.name):
            errors.append(f"{rel}: hash-suffixed workflow filename is forbidden")
        if path.name.startswith("catalog-"):
            errors.append(f"{rel}: catalog-prefixed workflow filename is forbidden")
        if text.startswith("# Central semantic shared-workflow family."):
            errors.append(f"{rel}: obsolete shared-family workflow remains")
        if "inputs.shared_variant" in text or "SHARED_VARIANT" in text:
            errors.append(f"{rel}: obsolete shared_variant runtime selector remains")
        for job_id in doc["jobs"]:
            if HASH_JOB_RE.match(str(job_id)):
                errors.append(f"{rel}: hash-prefixed job id remains: {job_id}")

    active_refs: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    repository_refs: dict[str, tuple[str, str]] = {}
    for manifest_path in sorted(REGISTRY.glob("*/manifest.json")):
        stats["manifests"] += 1
        rel_manifest = manifest_path.relative_to(ROOT).as_posix()
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel_manifest}: invalid JSON: {exc}")
            continue
        repo_info = manifest.get("repository") or {}
        repo = str(repo_info.get("full_name") or "")
        repo_id = str(repo_info.get("id") or "")
        if not repo or not repo_id:
            errors.append(f"{rel_manifest}: repository identity is incomplete")
            continue
        if manifest_path.parent.name != repo_id:
            errors.append(f"{rel_manifest}: directory id does not match repository id {repo_id}")
        for source_path, entry in (manifest.get("workflows") or {}).items():
            stats["registered_entries"] += 1
            if not isinstance(entry, dict):
                errors.append(f"{rel_manifest}:{source_path}: entry is not an object")
                continue
            if entry.get("status") != "active":
                continue
            stats["active_entries"] += 1
            binding = str(entry.get("binding") or "")
            central = str(entry.get("central_workflow") or "")
            if not central:
                errors.append(f"{rel_manifest}:{source_path}: active entry has no central_workflow")
                continue
            if binding == "shared-variant" or entry.get("shared_variant"):
                errors.append(f"{rel_manifest}:{source_path}: obsolete shared-variant binding remains")
            if binding not in {"repository", "curated"}:
                errors.append(f"{rel_manifest}:{source_path}: unknown active binding {binding!r}")
            if central not in workflow_docs:
                errors.append(f"{rel_manifest}:{source_path}: missing or invalid central workflow {central}")
                continue
            active_refs[central].append((repo, source_path, binding))
            if binding == "repository":
                stats["repository_bindings"] += 1
                expected = expected_repository_workflow(repo, source_path)
                if central != expected:
                    errors.append(f"{rel_manifest}:{source_path}: {central} != expected {expected}")
                prior = repository_refs.get(central)
                if prior is not None:
                    errors.append(f"{central}: referenced by both {prior[0]}:{prior[1]} and {repo}:{source_path}")
                repository_refs[central] = (repo, source_path)
            else:
                stats["curated_bindings"] += 1
                if central not in CURATED:
                    errors.append(f"{rel_manifest}:{source_path}: unrecognized curated workflow {central}")

    for central, rule in SEMANTIC_WORKFLOWS.items():
        doc = workflow_docs.get(central)
        if not doc:
            errors.append(f"{central}: semantic workflow is missing or invalid")
            continue
        expected_name = str(rule["name"])
        if doc.get("name") != expected_name:
            errors.append(f"{central}: semantic name {doc.get('name')!r} != {expected_name!r}")
        if "inputs.target_repository_name" not in str(doc.get("run-name") or ""):
            errors.append(f"{central}: run-name does not identify the target repository")
        dispatch = ((doc.get("on") or {}).get("workflow_dispatch") or {}) if isinstance(doc.get("on"), dict) else {}
        inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None
        if not isinstance(inputs, dict) or "target_repository_name" not in inputs:
            errors.append(f"{central}: semantic workflow is missing target_repository_name input")
        for job_id, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            target_secrets = secret_names(job) - GLOBAL_SECRETS
            if target_secrets and str(job_id) not in {"central_check_start", "central_check_finish"}:
                environment = job.get("environment")
                if "inputs.target_repository_name" not in str(environment or ""):
                    errors.append(f"{central}:{job_id}: target secrets do not use the target repository environment")
        for owner, group in concurrency_groups(doc):
            if "inputs.target_repository_name" not in group and "inputs.target_repository" not in group:
                errors.append(f"{central}:{owner}: semantic concurrency is not target-repository-scoped: {group}")

    literal_concurrency: dict[str, set[str]] = defaultdict(set)
    for central, (repo, source_path) in repository_refs.items():
        doc = workflow_docs.get(central)
        text = workflow_text.get(central, "")
        if not doc:
            continue
        repo_name = repo.rsplit("/", 1)[-1]
        if not str(doc.get("name") or "").startswith(repo_name + " · "):
            errors.append(f"{central}: workflow name must start with {repo_name} ·")
        if not str(doc.get("run-name") or "").startswith(repo_name + " · "):
            errors.append(f"{central}: run-name must start with {repo_name} ·")
        on_value = doc.get("on")
        if not isinstance(on_value, dict) or set(on_value) != {"workflow_dispatch"}:
            errors.append(f"{central}: repository executor must be workflow_dispatch-only")
        dispatch = (on_value or {}).get("workflow_dispatch") if isinstance(on_value, dict) else None
        inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None
        if not isinstance(inputs, dict) or "target_repository" not in inputs or "source_sha256" not in inputs:
            errors.append(f"{central}: repository executor is missing required dispatch inputs")
        for job_id, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            target_secrets = secret_names(job) - GLOBAL_SECRETS
            if target_secrets and str(job_id) not in {"central_check_start", "central_check_finish"} and job.get("environment") in (None, ""):
                errors.append(f"{central}:{job_id}: target secrets {sorted(target_secrets)} have no central environment")
        repo_markers = {repo_name.casefold(), slug(repo_name).casefold(), "${{ inputs.target_repository }}".casefold()}
        for owner, group in concurrency_groups(doc):
            lowered = group.casefold()
            if "shared_variant" in lowered or re.search(r"(?:^|[^0-9a-f])[0-9a-f]{16}(?:[^0-9a-f]|$)", lowered):
                errors.append(f"{central}:{owner}: hash/shared_variant concurrency is forbidden: {group}")
            if not any(marker in lowered for marker in repo_markers):
                errors.append(f"{central}:{owner}: concurrency is not repository-scoped: {group}")
            if "${{" not in group:
                literal_concurrency[group].add(repo)
        if re.search(r"\bshared_variant\b", text):
            errors.append(f"{central}: shared_variant text remains")

    for group, repos in literal_concurrency.items():
        if len(repos) > 1:
            errors.append(f"concurrency group {group!r} is shared by repositories: {sorted(repos)}")
    for central, refs in active_refs.items():
        if central not in CURATED and len(refs) != 1:
            errors.append(f"{central}: non-curated central workflow has {len(refs)} active references")

    referenced = set(active_refs) | CONTROLLER | CURATED
    for rel, text in workflow_text.items():
        if rel in referenced or rel in OBSOLETE_RUNTIME:
            continue
        if text.startswith("# Generated for ") or text.startswith("# Repository-scoped central workflow for "):
            stats["orphan_generated"] += 1
            errors.append(f"{rel}: generated repository workflow is not referenced by an active manifest")
    for rel in OBSOLETE_RUNTIME:
        if rel in workflow_text:
            errors.append(f"{rel}: obsolete one-off migration/repair workflow must be removed")

    sync_source = (ROOT / "scripts/sync_repository.py").read_text(encoding="utf-8")
    if "activate_repository_mode(core, repository)" not in sync_source:
        errors.append("scripts/sync_repository.py: repository mode is not mandatory")
    if "prune_shared_workflow_library" in sync_source:
        errors.append("scripts/sync_repository.py: obsolete shared-family garbage collector is still wired in")
    if "[central proxy]" in sync_source:
        errors.append("scripts/sync_repository.py: generated proxy name still exposes '[central proxy]'")
    dispatcher = (ROOT / "scripts/dispatch_request.py").read_text(encoding="utf-8")
    if "dispatch_inputs[\"shared_variant\"]" in dispatcher:
        errors.append("scripts/dispatch_request.py: dispatcher still sends shared_variant")
    return errors, dict(stats)


def main() -> int:
    errors, stats = audit()
    print(json.dumps({"stats": stats, "errors": errors}, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(f"workflow collection audit failed with {len(errors)} error(s)")
    print("workflow collection audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

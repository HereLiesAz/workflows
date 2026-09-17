#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

try:
    from . import sync_repository_catalog as core
    from .semantic_catalog import (
        GENERAL_CURATED_NAMES,
        OBSOLETE_WORKFLOWS,
        SEMANTIC_WORKFLOWS,
        TEMPORARY_CONTROLLER_WORKFLOWS,
        canonical_hash,
        curated_override_for_source,
        reviewed_override_for_source,
        workflow_display_name,
    )
except ImportError:
    import sync_repository_catalog as core
    from semantic_catalog import (
        GENERAL_CURATED_NAMES,
        OBSOLETE_WORKFLOWS,
        SEMANTIC_WORKFLOWS,
        TEMPORARY_CONTROLLER_WORKFLOWS,
        canonical_hash,
        curated_override_for_source,
        reviewed_override_for_source,
        workflow_display_name,
    )

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
WORKFLOWS = ROOT / ".github" / "workflows"
PROXY_MARKER = "# centralized-by: HereLiesAz/workflows"
TARGET_NAME_EXPR = "${{ inputs.target_repository_name }}"

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 4096
_yaml.indent(mapping=2, sequence=4, offset=2)


def load_yaml(path: Path) -> dict[str, Any]:
    doc = _yaml.load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} is not a YAML mapping")
    return doc


def dump_yaml(path: Path, doc: dict[str, Any], *, header: str | None = None) -> None:
    from io import StringIO

    out = StringIO()
    _yaml.dump(doc, out)
    text = out.getvalue()
    if header:
        text = header.rstrip() + "\n" + text
    path.write_text(text, encoding="utf-8")


def patch_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if old not in text:
        raise RuntimeError(f"Cannot patch {path.relative_to(ROOT)}: expected text not found: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def add_target_name_input(doc: dict[str, Any]) -> None:
    on_value = doc.get("on")
    if not isinstance(on_value, dict):
        raise RuntimeError("central workflow is not workflow_dispatch based")
    dispatch = on_value.get("workflow_dispatch")
    if dispatch is None:
        dispatch = CommentedMap()
        on_value["workflow_dispatch"] = dispatch
    if not isinstance(dispatch, dict):
        raise RuntimeError("workflow_dispatch is not a mapping")
    inputs = dispatch.get("inputs")
    if inputs is None:
        inputs = CommentedMap()
        dispatch["inputs"] = inputs
    if not isinstance(inputs, dict):
        raise RuntimeError("workflow_dispatch.inputs is not a mapping")
    if "target_repository_name" not in inputs:
        inputs["target_repository_name"] = CommentedMap(required=True, type="string")


def _scope_group(value: Any, repo_name: str | None, *, dynamic: bool) -> Any:
    if not isinstance(value, str):
        return value
    group = value
    if dynamic:
        if repo_name:
            group = re.sub(re.escape(repo_name) + r"$", TARGET_NAME_EXPR, group, flags=re.IGNORECASE)
        if "inputs.target_repository_name" not in group and "inputs.target_repository" not in group:
            group += f"-{TARGET_NAME_EXPR}"
        return group

    if not repo_name:
        return group
    markers = (repo_name.casefold(), re.sub(r"[^a-z0-9]+", "-", repo_name.casefold()).strip("-"))
    lowered = group.casefold()
    if not any(marker and marker in lowered for marker in markers) and "inputs.target_repository" not in lowered:
        group += f"-{repo_name}"
    return group


def scope_concurrency(doc: dict[str, Any], repo_name: str | None, *, dynamic: bool) -> bool:
    changed = False

    def fix(container: dict[str, Any]) -> None:
        nonlocal changed
        value = container.get("concurrency")
        if isinstance(value, str):
            new = _scope_group(value, repo_name, dynamic=dynamic)
            if new != value:
                container["concurrency"] = new
                changed = True
        elif isinstance(value, dict) and isinstance(value.get("group"), str):
            old = value["group"]
            new = _scope_group(old, repo_name, dynamic=dynamic)
            if new != old:
                value["group"] = new
                changed = True

    fix(doc)
    for job in (doc.get("jobs") or {}).values():
        if isinstance(job, dict):
            fix(job)
    return changed


def dynamicize_environment(doc: dict[str, Any], repo_name: str) -> bool:
    changed = False
    for job in (doc.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        env = job.get("environment")
        if isinstance(env, str) and env.casefold() == repo_name.casefold():
            job["environment"] = TARGET_NAME_EXPR
            changed = True
        elif isinstance(env, dict) and isinstance(env.get("name"), str) and env["name"].casefold() == repo_name.casefold():
            env["name"] = TARGET_NAME_EXPR
            changed = True
    return changed


def central_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest_path in sorted(REGISTRY.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        repo_info = manifest.get("repository") or {}
        repository = str(repo_info.get("full_name") or "")
        for source_path, entry in (manifest.get("workflows") or {}).items():
            if not isinstance(entry, dict) or entry.get("status") != "active":
                continue
            rows.append({
                "manifest_path": manifest_path,
                "manifest": manifest,
                "repository": repository,
                "repo_name": repository.rsplit("/", 1)[-1] if repository else "",
                "source_path": source_path,
                "entry": entry,
                "source_hash": str(entry.get("source_sha256") or ""),
                "central": str(entry.get("central_workflow") or ""),
            })
    return rows


def make_semantic_workflow(path: str, display_name: str, canonical_source_hash: str, rows: list[dict[str, Any]]) -> None:
    candidates = [row for row in rows if row["source_hash"] == canonical_source_hash and row["central"]]
    if not candidates:
        raise RuntimeError(f"No canonical source for {path}: {canonical_source_hash}")
    representative = candidates[0]
    source = ROOT / representative["central"]
    if not source.exists():
        raise RuntimeError(f"Canonical central workflow is missing: {representative['central']}")
    doc = load_yaml(source)
    add_target_name_input(doc)
    doc["name"] = display_name
    doc["run-name"] = f"{TARGET_NAME_EXPR} · {display_name}"
    dynamicize_environment(doc, representative["repo_name"])
    scope_concurrency(doc, representative["repo_name"], dynamic=True)

    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    dump_yaml(
        out,
        doc,
        header=(
            f"# Purpose-level central workflow: {display_name}.\n"
            "# Multiple repositories bind here only after their source behavior has been reviewed as equivalent."
        ),
    )


def clean_general_curated_workflows() -> None:
    for rel, display_name in GENERAL_CURATED_NAMES.items():
        path = ROOT / rel
        doc = load_yaml(path)
        add_target_name_input(doc)
        doc["name"] = display_name
        doc["run-name"] = f"{TARGET_NAME_EXPR} · {display_name}"
        dump_yaml(path, doc)


def delete_target_proxy(gh: core.GitHub, repository: str, source_path: str, default_branch: str) -> str:
    try:
        content, sha = gh.get_file(repository, source_path, ref=default_branch)
    except core.ApiError as exc:
        if "-> 404:" in str(exc):
            return "already-missing"
        raise
    if not content.startswith(PROXY_MARKER):
        raise RuntimeError(f"Refusing to delete non-proxy target file {repository}:{source_path}")
    endpoint = f"/repos/{repository}/contents/{urllib.parse.quote(source_path, safe='/')}"
    gh.json(
        "DELETE",
        endpoint,
        {
            "message": f"Remove obsolete workflow {source_path}",
            "sha": sha,
            "branch": default_branch,
        },
    )
    return "deleted"


def migrate_manifests(rows: list[dict[str, Any]], gh: core.GitHub | None) -> dict[str, int]:
    stats: Counter[str] = Counter()
    by_manifest: dict[Path, dict[str, Any]] = {}

    for row in rows:
        manifest_path: Path = row["manifest_path"]
        manifest = by_manifest.setdefault(manifest_path, row["manifest"])
        entry = (manifest.get("workflows") or {}).get(row["source_path"])
        if not isinstance(entry, dict):
            continue

        obsolete_reason = OBSOLETE_WORKFLOWS.get((row["repository"].casefold(), row["source_path"]))
        if obsolete_reason:
            if gh is not None:
                repo_info = manifest.get("repository") or {}
                result = delete_target_proxy(
                    gh,
                    row["repository"],
                    row["source_path"],
                    str(repo_info.get("default_branch") or "main"),
                )
                stats[f"target_proxy_{result}"] += 1
            entry["status"] = "obsolete"
            entry["reason"] = obsolete_reason
            for key in ("binding", "central_workflow", "implementation_sha256", "shared_variant"):
                entry.pop(key, None)
            stats["obsolete_entries"] += 1
            continue

        override = reviewed_override_for_source(row["source_hash"])
        if override:
            entry["binding"] = "curated"
            entry["central_workflow"] = override
            entry.pop("implementation_sha256", None)
            entry.pop("shared_variant", None)
            entry["semantic_purpose"] = workflow_display_name(override)
            if curated_override_for_source(row["source_hash"]):
                stats["curated_rebindings"] += 1
            else:
                stats["semantic_rebindings"] += 1

    for path, manifest in by_manifest.items():
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return dict(stats)


def prune_empty_incomplete_registry() -> int:
    removed = 0
    for manifest_path in sorted(REGISTRY.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        repo = manifest.get("repository") or {}
        if repo.get("full_name") and repo.get("id"):
            continue
        workflows = manifest.get("workflows") or {}
        if workflows:
            raise RuntimeError(f"Incomplete registry identity with workflow data: {manifest_path.relative_to(ROOT)}")
        shutil.rmtree(manifest_path.parent)
        removed += 1
    return removed


def repair_repository_concurrency() -> int:
    changed = 0
    seen: set[str] = set()
    for manifest_path in sorted(REGISTRY.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        repo = str((manifest.get("repository") or {}).get("full_name") or "")
        repo_name = repo.rsplit("/", 1)[-1] if repo else ""
        for entry in (manifest.get("workflows") or {}).values():
            if not isinstance(entry, dict) or entry.get("status") != "active" or entry.get("binding") != "repository":
                continue
            rel = str(entry.get("central_workflow") or "")
            if not rel or rel in seen:
                continue
            seen.add(rel)
            path = ROOT / rel
            if not path.exists():
                continue
            doc = load_yaml(path)
            if scope_concurrency(doc, repo_name, dynamic=False):
                dump_yaml(path, doc, header=f"# Generated for {repo}:{entry.get('registry_source', '')}.")
                changed += 1
    return changed


def prune_unreferenced_generated_workflows() -> int:
    referenced: set[str] = set()
    for manifest_path in REGISTRY.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in (manifest.get("workflows") or {}).values():
            if isinstance(entry, dict) and entry.get("status") == "active" and entry.get("central_workflow"):
                referenced.add(str(entry["central_workflow"]))

    removed = 0
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in referenced:
            continue
        text = path.read_text(encoding="utf-8")
        if text.startswith("# Generated for ") or text.startswith("# Repository-scoped central workflow for "):
            path.unlink()
            removed += 1
    return removed


def patch_controller_code() -> None:
    core_path = ROOT / "scripts" / "sync_repository_catalog.py"
    patch_once(
        core_path,
        "API_VERSION = \"2026-03-10\"\n",
        "try:\n    from .semantic_catalog import reviewed_override_for_source\nexcept ImportError:\n    from semantic_catalog import reviewed_override_for_source\n\nAPI_VERSION = \"2026-03-10\"\n",
    )
    patch_once(
        core_path,
        "        override = CATALOG_PATH_OVERRIDES.get(path)\n        if override:\n",
        "        override = reviewed_override_for_source(source_hash) or CATALOG_PATH_OVERRIDES.get(path)\n        if override:\n",
    )

    dispatch_path = ROOT / "scripts" / "dispatch_request.py"
    patch_once(
        dispatch_path,
        "from sync_repository import (\n    CENTRAL_REPOSITORY,\n    GitHub,\n    OWNER_ID,\n    OWNER_LOGIN,\n    ApiError,\n    load_manifest,\n)\n",
        "from sync_repository import (\n    CENTRAL_REPOSITORY,\n    GitHub,\n    OWNER_ID,\n    OWNER_LOGIN,\n    ApiError,\n    load_manifest,\n)\n\ntry:\n    from .semantic_catalog import uses_target_repository_name\nexcept ImportError:\n    from semantic_catalog import uses_target_repository_name\n",
    )
    patch_once(
        dispatch_path,
        "\n    body = {\"ref\": \"main\", \"inputs\": dispatch_inputs}\n",
        "\n    if uses_target_repository_name(central_workflow):\n        dispatch_inputs[\"target_repository_name\"] = repository.rsplit(\"/\", 1)[-1]\n\n    body = {\"ref\": \"main\", \"inputs\": dispatch_inputs}\n",
    )

    audit_path = ROOT / "scripts" / "audit_workflow_collection.py"
    patch_once(
        audit_path,
        "from ruamel.yaml import YAML\n",
        "from ruamel.yaml import YAML\n\ntry:\n    from .semantic_catalog import GENERAL_CURATED_NAMES, SEMANTIC_WORKFLOWS\nexcept ImportError:\n    from semantic_catalog import GENERAL_CURATED_NAMES, SEMANTIC_WORKFLOWS\n",
    )
    patch_once(
        audit_path,
        "CURATED = {\n    \".github/workflows/jules-dispatch.yml\",\n    \".github/workflows/jules-glee.yml\",\n    \".github/workflows/context-backup.yml\",\n    \".github/workflows/clear-cache.yml\",\n    \".github/workflows/morphont-publish.yml\",\n}\n",
        "CURATED = {\n    \".github/workflows/jules-dispatch.yml\",\n    \".github/workflows/jules-glee.yml\",\n    \".github/workflows/context-backup.yml\",\n    \".github/workflows/clear-cache.yml\",\n    \".github/workflows/morphont-publish.yml\",\n} | set(SEMANTIC_WORKFLOWS)\n",
    )
    semantic_check_anchor = "    literal_concurrency: dict[str, set[str]] = defaultdict(set)\n"
    semantic_checks = '''    for central, rule in SEMANTIC_WORKFLOWS.items():\n        doc = workflow_docs.get(central)\n        if not doc:\n            errors.append(f"{central}: semantic workflow is missing or invalid")\n            continue\n        expected_name = str(rule["name"])\n        if doc.get("name") != expected_name:\n            errors.append(f"{central}: semantic name {doc.get('name')!r} != {expected_name!r}")\n        if "inputs.target_repository_name" not in str(doc.get("run-name") or ""):\n            errors.append(f"{central}: run-name does not identify the target repository")\n        dispatch = ((doc.get("on") or {}).get("workflow_dispatch") or {}) if isinstance(doc.get("on"), dict) else {}\n        inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None\n        if not isinstance(inputs, dict) or "target_repository_name" not in inputs:\n            errors.append(f"{central}: semantic workflow is missing target_repository_name input")\n        for job_id, job in (doc.get("jobs") or {}).items():\n            if not isinstance(job, dict):\n                continue\n            target_secrets = secret_names(job) - GLOBAL_SECRETS\n            if target_secrets and str(job_id) not in {"central_check_start", "central_check_finish"}:\n                environment = job.get("environment")\n                if "inputs.target_repository_name" not in str(environment or ""):\n                    errors.append(f"{central}:{job_id}: target secrets do not use the target repository environment")\n        for owner, group in concurrency_groups(doc):\n            if "inputs.target_repository_name" not in group and "inputs.target_repository" not in group:\n                errors.append(f"{central}:{owner}: semantic concurrency is not target-repository-scoped: {group}")\n\n'''
    patch_once(audit_path, semantic_check_anchor, semantic_checks + semantic_check_anchor)

    validate_path = ROOT / ".github" / "workflows" / "validate-controller.yml"
    patch_once(
        validate_path,
        "            scripts/repository_workflow_mode.py \\\n",
        "            scripts/repository_workflow_mode.py \\\n            scripts/semantic_catalog.py \\\n",
    )

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace(
        "| Content-addressed catalog | Other centrally safe workflow logic, deduplicated by implementation hash across repositories |",
        "| Reviewed semantic catalog | Workflows that accomplish the same job share one named implementation after semantic review; hashes are only change-detection guards |",
    )
    text = text.replace(
        "Per-repository source state and bindings are stored under `registry/<repository-id>/`. Legacy per-repository `absorbed-<repo-id>-*.yml` executors are garbage-collected after successful catalog binding.",
        "Per-repository source state and bindings are stored under `registry/<repository-id>/`. Equivalent behavior is bound to one purpose-level workflow; repository-specific executors are kept only when the behavior is genuinely unique or still awaiting semantic review.",
    )
    readme.write_text(text, encoding="utf-8")


def remove_temporary_controller_workflows() -> int:
    removed = 0
    for rel in TEMPORARY_CONTROLLER_WORKFLOWS:
        path = ROOT / rel
        if path.exists():
            path.unlink()
            removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Collapse reviewed duplicate executors into purpose-level workflows.")
    parser.add_argument("--delete-target-proxies", action="store_true")
    args = parser.parse_args()

    rows = central_rows()
    before_files = len(list(WORKFLOWS.glob("*.y*ml")))
    before_repo_bindings = sum(1 for row in rows if row["entry"].get("binding") == "repository")

    for path, rule in SEMANTIC_WORKFLOWS.items():
        make_semantic_workflow(path, str(rule["name"]), canonical_hash(path), rows)
    clean_general_curated_workflows()

    gh = None
    if args.delete_target_proxies:
        token = os.environ.get("GH_TOKEN", "")
        if not token:
            raise RuntimeError("GH_TOKEN is required with --delete-target-proxies")
        gh = core.GitHub(token)

    manifest_stats = migrate_manifests(rows, gh)
    pruned_registry = prune_empty_incomplete_registry()
    repaired_concurrency = repair_repository_concurrency()
    patch_controller_code()
    temp_removed = remove_temporary_controller_workflows()
    orphan_removed = prune_unreferenced_generated_workflows()

    after_rows = central_rows()
    after_files = len(list(WORKFLOWS.glob("*.y*ml")))
    after_repo_bindings = sum(1 for row in after_rows if row["entry"].get("binding") == "repository")
    curated_bindings = sum(1 for row in after_rows if row["entry"].get("binding") == "curated")

    report = {
        "before_workflow_files": before_files,
        "after_workflow_files": after_files,
        "workflow_files_removed": before_files - after_files,
        "before_repository_bindings": before_repo_bindings,
        "after_repository_bindings": after_repo_bindings,
        "curated_bindings": curated_bindings,
        "semantic_workflows": len(SEMANTIC_WORKFLOWS),
        "empty_registry_directories_removed": pruned_registry,
        "repository_concurrency_files_repaired": repaired_concurrency,
        "temporary_controller_workflows_removed": temp_removed,
        "orphan_generated_workflows_removed": orphan_removed,
        **manifest_stats,
    }
    Path("/tmp/semantic-migration-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

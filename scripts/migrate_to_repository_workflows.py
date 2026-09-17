#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REGISTRY = ROOT / "registry"
SHARED_HEADER = "# Central semantic shared-workflow family."

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)


def load_yaml(text: str) -> Any:
    return yaml.load(text)


def dump_yaml(data: Any) -> str:
    from io import StringIO

    out = StringIO()
    yaml.dump(data, out)
    return out.getvalue()


def slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return value or "workflow"


def dedicated_path(repository: str, source_path: str) -> str:
    repo_name = repository.split("/", 1)[-1]
    source_stem = PurePosixPath(source_path).stem
    return f".github/workflows/{slug(repo_name)}-{slug(source_stem)}.yml"


def expression_body(value: Any) -> str:
    text = str(value).strip()
    if text.startswith("${{") and text.endswith("}}"):
        return text[3:-2].strip()
    return text


def strip_variant_condition(value: Any, variant: str) -> Any:
    if value is None:
        return None
    body = expression_body(value)
    selector = f"inputs.shared_variant == '{variant}'"
    if body == selector:
        return None

    suffix = f") && ({selector})"
    if body.startswith("(") and body.endswith(suffix):
        original = body[1 : -len(suffix)]
        return "${{ " + original + " }}"

    # Defensive fallback for any family produced by an older compiler revision.
    body = re.sub(
        rf"\s*&&\s*\(?{re.escape(selector)}\)?\s*$",
        "",
        body,
    ).strip()
    body = re.sub(
        rf"^\(?{re.escape(selector)}\)?\s*&&\s*",
        "",
        body,
    ).strip()
    if body in {"", "()"}:
        return None
    return "${{ " + body + " }}"


def rewrite_variant_references(value: Any, prefix: str, variant: str) -> Any:
    if isinstance(value, str):
        return value.replace(f"needs.{prefix}", "needs.")
    if isinstance(value, dict):
        out = CommentedMap()
        for key, item in value.items():
            if key == "needs":
                if isinstance(item, str):
                    out[key] = item[len(prefix) :] if item.startswith(prefix) else item
                elif isinstance(item, list):
                    out[key] = CommentedSeq(
                        str(dep)[len(prefix) :] if str(dep).startswith(prefix) else str(dep)
                        for dep in item
                    )
                else:
                    out[key] = copy.deepcopy(item)
            elif key == "if":
                cleaned = strip_variant_condition(item, variant)
                if cleaned is not None:
                    out[key] = cleaned
            else:
                out[key] = rewrite_variant_references(item, prefix, variant)
        return out
    if isinstance(value, list):
        return CommentedSeq(rewrite_variant_references(item, prefix, variant) for item in value)
    return copy.deepcopy(value)


def flatten_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from flatten_strings(key)
            yield from flatten_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)


def scope_concurrency(value: Any, repo_name: str) -> Any:
    if isinstance(value, str):
        text = value
        text = text.replace("${{ inputs.target_repository }}", repo_name)
        text = text.replace("${{ inputs.shared_variant }}", repo_name)
        return text
    if isinstance(value, dict):
        out = CommentedMap(copy.deepcopy(value))
        if "group" in out:
            out["group"] = scope_concurrency(out["group"], repo_name)
        return out
    return copy.deepcopy(value)


def extract_repository_workflow(
    family_text: str,
    repository: str,
    source_path: str,
    workflow_name: str,
    variant: str,
) -> str:
    family = load_yaml(family_text)
    if not isinstance(family, dict):
        raise RuntimeError("shared family is not a workflow mapping")

    on_value = family.get("on") or {}
    dispatch = on_value.get("workflow_dispatch") if isinstance(on_value, dict) else None
    if not isinstance(dispatch, dict):
        raise RuntimeError("shared family has no workflow_dispatch mapping")
    inputs = CommentedMap(copy.deepcopy(dispatch.get("inputs") or {}))
    inputs.pop("shared_variant", None)

    prefix = f"v_{variant}__"
    family_jobs = family.get("jobs") or {}
    jobs = CommentedMap()
    repo_name = repository.split("/", 1)[-1]

    for old_id, raw_job in family_jobs.items():
        old_id = str(old_id)
        if not old_id.startswith(prefix):
            continue
        new_id = old_id[len(prefix) :]
        job = rewrite_variant_references(raw_job, prefix, variant)
        if not isinstance(job, dict):
            raise RuntimeError(f"invalid job {old_id} in shared family")
        if "concurrency" in job:
            job["concurrency"] = scope_concurrency(job["concurrency"], repo_name)

        # Repository environments are the central secret namespace. Repository
        # secrets remain available, while environment secrets can override them
        # for one target without exposing that target's credentials to another.
        if (
            new_id not in {"central_check_start", "central_check_finish"}
            and "environment" not in job
            and any("secrets." in text or "github.token" in text for text in flatten_strings(job))
        ):
            job["environment"] = repo_name

        jobs[new_id] = job

    if not jobs:
        raise RuntimeError(f"variant {variant} has no jobs")
    if "central_check_start" not in jobs or "central_check_finish" not in jobs:
        raise RuntimeError(f"variant {variant} is missing central reporting jobs")

    doc = CommentedMap()
    doc["name"] = f"{repo_name} · {workflow_name}"
    doc["run-name"] = f"{repo_name} · {workflow_name}"
    doc["on"] = CommentedMap({"workflow_dispatch": CommentedMap({"inputs": inputs})})
    doc["jobs"] = jobs

    return (
        f"# Generated for {repository}:{source_path}.\n"
        "# Edit the registered source or synchronizer, not this compiled workflow.\n"
        + dump_yaml(doc)
    )


def main() -> int:
    migrated = 0
    created: set[str] = set()
    former_shared_paths: set[str] = set()

    manifest_paths = sorted(REGISTRY.glob("*/manifest.json"))
    manifests: list[tuple[Path, dict[str, Any]]] = []
    for manifest_path in manifest_paths:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifests.append((manifest_path, manifest))

        repository = str((manifest.get("repository") or {}).get("full_name") or "")
        if not repository:
            continue
        workflows = manifest.get("workflows") or {}
        changed = False

        for source_path, entry in workflows.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("status") != "active" or entry.get("binding") != "shared-variant":
                continue

            old_central = str(entry.get("central_workflow") or "")
            variant = str(entry.get("shared_variant") or "")
            if not old_central or not variant:
                raise RuntimeError(f"incomplete shared binding: {manifest_path}:{source_path}")

            old_file = ROOT / old_central
            if not old_file.is_file():
                raise RuntimeError(f"missing shared family {old_central}")
            family_text = old_file.read_text(encoding="utf-8")
            new_central = dedicated_path(repository, source_path)
            if new_central in created:
                raise RuntimeError(f"dedicated workflow collision: {new_central}")

            compiled = extract_repository_workflow(
                family_text,
                repository,
                source_path,
                str(entry.get("name") or PurePosixPath(source_path).name),
                variant,
            )
            destination = ROOT / new_central
            destination.write_text(compiled, encoding="utf-8")
            created.add(new_central)
            former_shared_paths.add(old_central)

            entry["binding"] = "repository"
            entry["central_workflow"] = new_central
            entry.pop("shared_variant", None)
            migrated += 1
            changed = True

        if changed:
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    referenced: set[str] = set()
    for manifest_path, _ in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in (manifest.get("workflows") or {}).values():
            if isinstance(entry, dict) and entry.get("status") == "active" and entry.get("central_workflow"):
                referenced.add(str(entry["central_workflow"]))

    removed = 0
    for old_central in sorted(former_shared_paths):
        if old_central in referenced:
            continue
        path = ROOT / old_central
        if path.is_file() and path.read_text(encoding="utf-8").startswith(SHARED_HEADER):
            path.unlink()
            removed += 1

    print(json.dumps({
        "migrated_bindings": migrated,
        "created_repository_workflows": len(created),
        "removed_shared_families": removed,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

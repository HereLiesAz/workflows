#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
from typing import Any

try:
    from .sync_repository_catalog import CENTRAL_REPOSITORY, ApiError, GitHub, dump_yaml, load_yaml
except ImportError:
    from sync_repository_catalog import CENTRAL_REPOSITORY, ApiError, GitHub, dump_yaml, load_yaml

GENERATED_HEADER = "# Central semantic shared-workflow family."
VARIANT_JOB = re.compile(r"^v_([0-9a-f]{16})__")


def variant_guard_script(variants: set[str]) -> str:
    choices = "|".join(sorted(variants))
    return (
        "set -euo pipefail\n"
        'case "$SHARED_VARIANT" in\n'
        f"  {choices}) ;;\n"
        '  *) echo "Unknown shared workflow variant: $SHARED_VARIANT" >&2; exit 1 ;;\n'
        "esac\n"
    )


def active_variant_references(gh: GitHub) -> dict[str, set[str]]:
    references: dict[str, set[str]] = {}
    registry = gh.contents(CENTRAL_REPOSITORY, "registry", ref="main")
    if not isinstance(registry, list):
        raise RuntimeError("central registry is not a directory")

    for item in registry:
        if not isinstance(item, dict) or item.get("type") != "dir":
            continue
        manifest_path = f"{item['path']}/manifest.json"
        try:
            text, _ = gh.get_file(CENTRAL_REPOSITORY, manifest_path, ref="main")
        except ApiError as exc:
            if "-> 404:" in str(exc):
                continue
            raise
        manifest = json.loads(text)
        for entry in (manifest.get("workflows") or {}).values():
            if not isinstance(entry, dict):
                continue
            if entry.get("status") != "active" or entry.get("binding") != "shared-variant":
                continue
            central_workflow = str(entry.get("central_workflow") or "")
            shared_variant = str(entry.get("shared_variant") or "")
            if not central_workflow or not shared_variant:
                raise RuntimeError(f"active shared-variant binding is incomplete in {manifest_path}")
            references.setdefault(central_workflow, set()).add(shared_variant)
    return references


def delete_file(gh: GitHub, path: str, sha: str, message: str) -> None:
    quoted = urllib.parse.quote(path, safe="/")
    gh.json(
        "DELETE",
        f"/repos/{CENTRAL_REPOSITORY}/contents/{quoted}",
        {"message": message, "sha": sha, "branch": "main"},
    )


def prune_shared_workflow_library(gh: GitHub, *, dry_run: bool = False) -> dict[str, Any]:
    references = active_variant_references(gh)
    workflow_items = gh.contents(CENTRAL_REPOSITORY, ".github/workflows", ref="main")
    if not isinstance(workflow_items, list):
        raise RuntimeError("central workflow directory is not a directory")

    actions: list[dict[str, Any]] = []
    generated_paths: set[str] = set()

    for item in workflow_items:
        if not isinstance(item, dict) or item.get("type") != "file":
            continue
        path = str(item.get("path") or "")
        if not path.endswith((".yml", ".yaml")):
            continue
        text, sha = gh.get_file(CENTRAL_REPOSITORY, path, ref="main")
        if not text.startswith(GENERATED_HEADER):
            continue

        generated_paths.add(path)
        keep = references.get(path, set())
        doc = load_yaml(text)
        if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
            raise RuntimeError(f"generated semantic workflow is invalid: {path}")
        jobs = doc["jobs"]
        current = {
            match.group(1)
            for job_id in jobs
            if (match := VARIANT_JOB.match(str(job_id)))
        }
        missing = keep - current
        if missing:
            raise RuntimeError(
                f"{path} is missing active registered variants: {sorted(missing)}"
            )

        if not keep:
            actions.append({"path": path, "action": "delete-orphan", "variants": sorted(current)})
            if not dry_run:
                delete_file(
                    gh,
                    path,
                    sha,
                    f"Remove orphaned semantic workflow {path.rsplit('/', 1)[-1]}",
                )
            continue

        stale = current - keep
        if not stale:
            continue

        for job_id in list(jobs):
            match = VARIANT_JOB.match(str(job_id))
            if match and match.group(1) in stale:
                del jobs[job_id]

        guard = jobs.get("shared_variant_guard")
        if not isinstance(guard, dict):
            raise RuntimeError(f"generated semantic workflow has no guard: {path}")
        steps = guard.get("steps") or []
        if not steps or not isinstance(steps[0], dict):
            raise RuntimeError(f"generated semantic workflow guard shape changed: {path}")
        steps[0]["run"] = variant_guard_script(keep)

        header = (
            "# Central semantic shared-workflow family.\n"
            "# Public identity is the filename; implementation hashes are internal registry metadata only.\n"
            "# Do not edit generated variant jobs by hand; update the source workflow or synchronizer.\n"
        )
        new_text = header + dump_yaml(doc)
        actions.append({
            "path": path,
            "action": "prune",
            "removed_variants": sorted(stale),
            "kept_variants": sorted(keep),
        })
        if not dry_run:
            gh.put_file(
                CENTRAL_REPOSITORY,
                path,
                new_text,
                f"Prune stale variants from {path.rsplit('/', 1)[-1]}",
                branch="main",
            )

    missing_files = sorted(set(references) - generated_paths)
    if missing_files:
        raise RuntimeError(
            "active registry bindings point at missing/non-generated semantic workflows: "
            + ", ".join(missing_files)
        )

    return {
        "generated_workflows": len(generated_paths),
        "referenced_workflows": len(references),
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Garbage-collect semantic shared workflow variants.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    result = prune_shared_workflow_library(gh, dry_run=args.dry_run)
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
REGISTRY_DIR = ROOT / "registry"
SYNC_SCRIPT = ROOT / "scripts" / "sync_repository_catalog.py"
ONBOARDING_DOC = ROOT / "docs" / "REPOSITORY_ONBOARDING.md"
LEGACY_CATALOG_RE = re.compile(r"^catalog-([0-9a-f]{16})\.ya?ml$")
SHARED_SUFFIX = " [shared catalog]"

yaml = YAML(typ="safe")


def catalog_name_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return slug[:72].rstrip("-") or "workflow"


def workflow_name(text: str, filename: str) -> str:
    doc = yaml.load(text)
    if not isinstance(doc, dict):
        raise RuntimeError(f"{filename}: generated catalog is not a YAML mapping")
    name = str(doc.get("name") or filename)
    if name.endswith(SHARED_SUFFIX):
        name = name[: -len(SHARED_SUFFIX)]
    return name.strip() or "workflow"


def rename_legacy_catalogs() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for source in sorted(WORKFLOWS_DIR.iterdir()):
        match = LEGACY_CATALOG_RE.fullmatch(source.name)
        if not match:
            continue

        hash16 = match.group(1)
        text = source.read_text(encoding="utf-8")
        name = workflow_name(text, source.name)
        destination = WORKFLOWS_DIR / f"catalog-{catalog_name_slug(name)}-{hash16}.yml"

        if destination.exists():
            if destination.read_text(encoding="utf-8") != text:
                raise RuntimeError(
                    f"Refusing rename collision: {source.relative_to(ROOT)} -> {destination.relative_to(ROOT)}"
                )
            source.unlink()
        else:
            source.rename(destination)

        mapping[source.relative_to(ROOT).as_posix()] = destination.relative_to(ROOT).as_posix()
    return mapping


def rewrite_manifests(mapping: dict[str, str]) -> tuple[int, int]:
    changed_manifests = 0
    changed_bindings = 0
    if not REGISTRY_DIR.exists():
        return changed_manifests, changed_bindings

    for manifest_path in sorted(REGISTRY_DIR.glob("*/manifest.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        changed = False
        workflows = data.get("workflows") or {}
        if not isinstance(workflows, dict):
            continue

        for entry in workflows.values():
            if not isinstance(entry, dict):
                continue
            current = entry.get("central_workflow")
            replacement = mapping.get(str(current))
            if replacement and replacement != current:
                entry["central_workflow"] = replacement
                changed = True
                changed_bindings += 1

        if changed:
            manifest_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            changed_manifests += 1

    return changed_manifests, changed_bindings


def patch_synchronizer() -> None:
    text = SYNC_SCRIPT.read_text(encoding="utf-8")

    old_function = '''def catalog_workflow_path(doc: dict[str, Any]) -> str:\n    return f".github/workflows/catalog-{catalog_hash(doc)[:16]}.yml"\n'''
    new_function = '''def catalog_name_slug(name: str) -> str:\n    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")\n    return slug[:72].rstrip("-") or "workflow"\n\n\ndef catalog_workflow_path(doc: dict[str, Any], workflow_name: str) -> str:\n    return f".github/workflows/catalog-{catalog_name_slug(workflow_name)}-{catalog_hash(doc)[:16]}.yml"\n\n\ndef discover_catalog_workflow_paths(gh: GitHub) -> dict[str, str]:\n    listing = gh.contents(CENTRAL_REPOSITORY, ".github/workflows", ref="main")\n    if not isinstance(listing, list):\n        raise RuntimeError("Central .github/workflows is not a directory")\n\n    by_hash: dict[str, str] = {}\n    for item in listing:\n        if item.get("type") != "file":\n            continue\n        name = str(item.get("name", ""))\n        match = re.fullmatch(r"catalog-(?:.+-)?([0-9a-f]{16})\\.ya?ml", name)\n        if not match:\n            continue\n        hash16 = match.group(1)\n        path = str(item.get("path", ""))\n        current = by_hash.get(hash16)\n        if current is None or re.fullmatch(r"\\.github/workflows/catalog-[0-9a-f]{16}\\.ya?ml", current):\n            by_hash[hash16] = path\n    return by_hash\n'''
    if old_function not in text:
        if new_function not in text:
            raise RuntimeError("Could not find the catalog naming function to patch")
    else:
        text = text.replace(old_function, new_function, 1)

    old_results = '''    results: list[dict[str, Any]] = []\n    if worker_url and not dry_run:\n'''
    new_results = '''    results: list[dict[str, Any]] = []\n    catalog_paths = discover_catalog_workflow_paths(gh)\n    if worker_url and not dry_run:\n'''
    if old_results in text:
        text = text.replace(old_results, new_results, 1)
    elif new_results not in text:
        raise RuntimeError("Could not add central catalog discovery to synchronizer")

    old_path = '''        c_hash = catalog_hash(expanded)\n        central_workflow = catalog_workflow_path(expanded)\n'''
    new_path = '''        c_hash = catalog_hash(expanded)\n        central_workflow = catalog_paths.get(c_hash[:16]) or catalog_workflow_path(expanded, workflow_name)\n        catalog_paths[c_hash[:16]] = central_workflow\n'''
    if old_path in text:
        text = text.replace(old_path, new_path, 1)
    elif new_path not in text:
        raise RuntimeError("Could not patch generated catalog path selection")

    SYNC_SCRIPT.write_text(text, encoding="utf-8")


def patch_docs() -> None:
    text = ONBOARDING_DOC.read_text(encoding="utf-8")
    old = "One shared workflow keyed by implementation hash; identical logic can be reused by multiple repos"
    new = "One descriptively named shared workflow with an implementation-hash suffix; identical logic can be reused by multiple repos"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("Could not update catalog naming documentation")
    ONBOARDING_DOC.write_text(text, encoding="utf-8")


def validate(mapping: dict[str, str]) -> None:
    legacy = [path.name for path in WORKFLOWS_DIR.iterdir() if LEGACY_CATALOG_RE.fullmatch(path.name)]
    if legacy:
        raise RuntimeError(f"Legacy hash-only catalog filenames remain: {legacy}")

    for manifest_path in REGISTRY_DIR.glob("*/manifest.json"):
        text = manifest_path.read_text(encoding="utf-8")
        leftovers = [old for old in mapping if old in text]
        if leftovers:
            raise RuntimeError(f"{manifest_path.relative_to(ROOT)} still references {leftovers[0]}")

    sync_text = SYNC_SCRIPT.read_text(encoding="utf-8")
    if 'catalog-{catalog_hash(doc)[:16]}.yml' in sync_text:
        raise RuntimeError("Synchronizer still contains the hash-only catalog filename generator")
    if "discover_catalog_workflow_paths(gh)" not in sync_text:
        raise RuntimeError("Synchronizer is not preserving cross-repository hash deduplication")


def main() -> int:
    mapping = rename_legacy_catalogs()
    changed_manifests, changed_bindings = rewrite_manifests(mapping)
    patch_synchronizer()
    patch_docs()
    validate(mapping)

    print(f"Renamed catalog workflows: {len(mapping)}")
    print(f"Updated registry manifests: {changed_manifests}")
    print(f"Updated registry bindings: {changed_bindings}")
    for old, new in sorted(mapping.items()):
        print(f"{old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

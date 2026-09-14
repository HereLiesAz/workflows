#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from shared_workflow_library import (
    build_shared_family,
    load_yaml,
    semantic_family_slug,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REGISTRY = ROOT / "registry"
CORE = ROOT / "scripts" / "sync_repository_catalog.py"
VALIDATOR = WORKFLOWS / "validate-controller.yml"

CURATED_RENAMES = {
    ".github/workflows/catalog-jules-dispatch.yml": ".github/workflows/jules-dispatch.yml",
    ".github/workflows/catalog-jules-glee.yml": ".github/workflows/jules-glee.yml",
    ".github/workflows/catalog-context-backup.yml": ".github/workflows/context-backup.yml",
    ".github/workflows/catalog-clear-cache.yml": ".github/workflows/clear-cache.yml",
}

CATALOG_FILE_RE = re.compile(r"^catalog-(?P<name>.+)-(?P<variant>[0-9a-f]{16})\.ya?ml$")
HASH_ONLY_RE = re.compile(r"^catalog-(?P<variant>[0-9a-f]{16})\.ya?ml$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_manifests() -> dict[Path, dict[str, Any]]:
    manifests: dict[Path, dict[str, Any]] = {}
    for path in sorted(REGISTRY.glob("*/manifest.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError(f"invalid manifest: {path}")
        manifests[path] = data
    return manifests


def references_by_central(manifests: dict[Path, dict[str, Any]]) -> dict[str, list[tuple[Path, str, dict[str, Any]]]]:
    refs: dict[str, list[tuple[Path, str, dict[str, Any]]]] = {}
    for manifest_path, manifest in manifests.items():
        for source_path, entry in (manifest.get("workflows") or {}).items():
            if not isinstance(entry, dict):
                continue
            central = entry.get("central_workflow")
            if isinstance(central, str) and central:
                refs.setdefault(central, []).append((manifest_path, str(source_path), entry))
    return refs


def workflow_name(text: str, fallback: str) -> str:
    doc = load_yaml(text)
    if not isinstance(doc, dict):
        return fallback
    value = str(doc.get("name") or fallback)
    return re.sub(r"\s*\[shared catalog\]\s*$", "", value, flags=re.IGNORECASE).strip()


def patch_core() -> None:
    text = CORE.read_text(encoding="utf-8")

    import_anchor = "from ruamel.yaml.comments import CommentedMap, CommentedSeq\n"
    semantic_import = '''from ruamel.yaml.comments import CommentedMap, CommentedSeq

try:
    from .shared_workflow_library import add_shared_variant, semantic_family_slug, shared_workflow_path
except ImportError:
    from shared_workflow_library import add_shared_variant, semantic_family_slug, shared_workflow_path
'''
    if "from .shared_workflow_library import" not in text:
        if import_anchor not in text:
            raise RuntimeError("cannot locate semantic-library import anchor")
        text = text.replace(import_anchor, semantic_import, 1)

    old_overrides = '''CATALOG_PATH_OVERRIDES = {
    ".github/workflows/jules-dispatch.yml": ".github/workflows/catalog-jules-dispatch.yml",
    ".github/workflows/jules-glee.yml": ".github/workflows/catalog-jules-glee.yml",
    ".github/workflows/backup.yml": ".github/workflows/catalog-context-backup.yml",
    ".github/workflows/clear_cache.yml": ".github/workflows/catalog-clear-cache.yml",
}'''
    new_overrides = '''CATALOG_PATH_OVERRIDES = {
    ".github/workflows/jules-dispatch.yml": ".github/workflows/jules-dispatch.yml",
    ".github/workflows/jules-glee.yml": ".github/workflows/jules-glee.yml",
    ".github/workflows/backup.yml": ".github/workflows/context-backup.yml",
    ".github/workflows/clear_cache.yml": ".github/workflows/clear-cache.yml",
}'''
    if old_overrides in text:
        text = text.replace(old_overrides, new_overrides, 1)
    elif new_overrides not in text:
        raise RuntimeError("cannot locate curated path overrides")

    text = text.replace("    catalog_paths = discover_catalog_workflow_paths(gh)\n", "")

    legacy_anchor = '''        workflow_name = str(parsed.get("name") or PurePosixPath(path).name)
        slug = slugify(path)
        registry_source = f"registry/{repo_id}/{slug}.source.yml"
'''
    legacy_block = '''        workflow_name = str(parsed.get("name") or PurePosixPath(path).name)
        slug = slugify(path)
        registry_source = f"registry/{repo_id}/{slug}.source.yml"

        if "glee" in workflow_name.casefold() and path != ".github/workflows/jules-glee.yml":
            blockers = [
                "legacy Glee workflow disabled: Glee may only use the canonical repoless Jules API audit and one PR comment"
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
'''
    if "legacy Glee workflow disabled" not in text:
        if legacy_anchor not in text:
            raise RuntimeError("cannot locate workflow-name classification anchor")
        text = text.replace(legacy_anchor, legacy_block, 1)

    text = text.replace('"catalog": "curated",', '"binding": "curated",')

    block_re = re.compile(
        r'''        c_hash = catalog_hash\(expanded\)\n'''
        r'''        central_workflow = catalog_paths\.get\(c_hash\[:16\]\) or catalog_workflow_path\(expanded, workflow_name\)\n'''
        r'''        catalog_paths\[c_hash\[:16\]\] = central_workflow\n'''
        r'''        try:\n'''
        r'''            compiled = compile_central\(dump_yaml\(expanded\), \{"full_name": "HereLiesAz/workflows-catalog", "private": True\}, f"catalog/\{c_hash\}", workflow_name\)\n'''
        r'''            proxy = build_proxy\(source_text, path, source_hash, workflow_name\)\n'''
        r'''        except Exception as exc:\n'''
        r'''            workflows_manifest\[path\] = \{"status": "local", "source_sha256": source_hash, "name": workflow_name, "blockers": \[str\(exc\)\], "registry_source": registry_source, "updated_at": now_iso\(\)\}\n'''
        r'''            if not dry_run and is_proxy:\n'''
        r'''                gh\.put_file\(repo\["full_name"\], path, source_text, f"Restore local workflow \{path\}; catalog compilation failed", branch=default_branch\)\n'''
        r'''            results\.append\(\{"path": path, "status": "local", "blockers": \[str\(exc\)\]\}\)\n'''
        r'''            continue\n\n'''
        r'''        workflows_manifest\[path\] = \{"status": "active", "name": workflow_name, "source_sha256": source_hash, "registry_source": registry_source, "central_workflow": central_workflow, "catalog": "content-addressed", "catalog_hash": c_hash, "updated_at": now_iso\(\)\}\n'''
        r'''        if not dry_run:\n'''
        r'''            gh\.put_file\(CENTRAL_REPOSITORY, registry_source, source_text, f"Register \{repo\['full_name'\]\}:\{path\}", branch="main"\)\n'''
        r'''            gh\.put_file\(CENTRAL_REPOSITORY, central_workflow, compiled, f"Update shared workflow catalog \{c_hash\[:16\]\}", branch="main"\)\n'''
        r'''            gh\.put_file\(repo\["full_name"\], path, proxy, f"Refresh \{path\} from shared catalog via \{CENTRAL_REPOSITORY\}", branch=default_branch\)\n'''
        r'''        results\.append\(\{"path": path, "status": "catalog", "central_workflow": central_workflow, "catalog_hash": c_hash, "source_sha256": source_hash\}\)'''
    )

    replacement = '''        implementation_hash = catalog_hash(expanded)
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
        })'''

    text, count = block_re.subn(replacement, text)
    if count == 0 and "implementation_sha256" not in text:
        raise RuntimeError("cannot locate content-addressed catalog binding block")
    if count > 1:
        raise RuntimeError(f"unexpected catalog binding replacement count: {count}")

    CORE.write_text(text, encoding="utf-8")


def patch_dispatch_workflow() -> None:
    path = WORKFLOWS / "jules-dispatch.yml"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'''          if event_name == "pull_request":\n.*?\n          elif event_name == "issues":''',
        re.S,
    )
    replacement = '''          if event_name == "pull_request":
              # Ordinary PR-open auditing belongs exclusively to Glee. Jules
              # Dispatch only responds to explicit @jules PR interactions.
              pass

          elif event_name == "issues":'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1 and "Ordinary PR-open auditing belongs exclusively to Glee" not in text:
        raise RuntimeError("could not remove automatic PR-open Jules Dispatch path")
    path.write_text(text, encoding="utf-8")


def patch_validator_paths() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    text = text.replace(".github/workflows/catalog-jules-glee.yml", ".github/workflows/jules-glee.yml")
    # Glee now intentionally contains the words sourceContext and pullRequest in
    # runtime API assertions, so validate the payload and assertions rather than
    # banning those tokens globally.
    text = text.replace(
        "          assert 'sourceContext' not in glee_source\n"
        "          assert 'sources/github/' not in glee_source\n"
        "          assert 'AUTO_CREATE_PR' not in glee_source\n",
        "          assert 'has(\"sourceContext\") | not' in glee_source\n"
        "          assert 'sources/github/' not in glee_source\n"
        "          assert 'AUTO_CREATE_PR' not in glee_source\n"
        "          assert '.outputs[]?; .pullRequest? != null' in glee_source\n"
        "          assert '.activities[]?.artifacts[]?; .changeSet? != null' in glee_source\n",
    )
    text = text.replace(
        "          assert 'source_path == \".github/workflows/jules-dispatch.yml\" and event_name == \"pull_request\"' in dispatcher_source\n",
        "          assert 'source_path == \".github/workflows/jules-dispatch.yml\" and event_name == \"pull_request\"' in dispatcher_source\n"
        "          assert 'source_path == \".github/workflows/jules-glee.yml\"' in dispatcher_source\n"
        "          assert 'event_name != \"pull_request_target\"' in dispatcher_source\n"
        "          assert 'shared_variant' in dispatcher_source\n",
    )
    text = text.replace("for path in Path('.github/workflows').glob('catalog-*.y*ml'):", "for path in Path('.github/workflows').glob('*.y*ml'):")
    VALIDATOR.write_text(text, encoding="utf-8")


def main() -> int:
    manifests = load_manifests()
    refs = references_by_central(manifests)

    # Curated workflows have permanent semantic identities.
    for old_rel, new_rel in CURATED_RENAMES.items():
        old = ROOT / old_rel
        new = ROOT / new_rel
        if old.exists():
            if new.exists():
                raise RuntimeError(f"curated destination already exists: {new_rel}")
            old.rename(new)

    generated: dict[str, dict[str, Any]] = {}
    legacy_glee_paths: set[str] = set()

    for path in sorted(WORKFLOWS.glob("catalog-*.y*ml")):
        filename = path.name
        match = CATALOG_FILE_RE.match(filename) or HASH_ONLY_RE.match(filename)
        if not match:
            raise RuntimeError(f"unrecognized catalog workflow filename: {filename}")
        old_rel = rel(path)
        variant = match.group("variant")
        text = path.read_text(encoding="utf-8")
        entries = refs.get(old_rel, [])
        source_path = entries[0][1] if entries else f".github/workflows/{match.groupdict().get('name') or 'workflow'}.yml"
        entry_name = str(entries[0][2].get("name") or "") if entries else ""
        name = entry_name or workflow_name(text, filename)
        family = semantic_family_slug(name, source_path, text)

        if family == "legacy-glee":
            legacy_glee_paths.add(old_rel)
            continue

        family_path = f".github/workflows/{family}.yml"
        bucket = generated.setdefault(family_path, {"family": family, "variants": {}, "old_paths": set()})
        existing = bucket["variants"].get(variant)
        if existing is not None and existing != text:
            raise RuntimeError(f"variant collision in {family}: {variant}")
        bucket["variants"][variant] = text
        bucket["old_paths"].add(old_rel)

    old_to_new: dict[str, tuple[str, str]] = {}
    for family_path, info in sorted(generated.items()):
        destination = ROOT / family_path
        if destination.exists():
            raise RuntimeError(f"semantic family destination already exists: {family_path}")
        variants = sorted(info["variants"].items())
        destination.write_text(build_shared_family(info["family"], variants), encoding="utf-8")
        for old_rel in info["old_paths"]:
            variant_match = CATALOG_FILE_RE.match(Path(old_rel).name) or HASH_ONLY_RE.match(Path(old_rel).name)
            if variant_match is None:
                raise RuntimeError(f"cannot recover variant from {old_rel}")
            old_to_new[old_rel] = (family_path, variant_match.group("variant"))

    # Rewrite registry bindings before removing old workflow files.
    changed_manifests = 0
    binding_count = 0
    blocked_legacy = 0
    for manifest_path, manifest in manifests.items():
        changed = False
        for source_path, entry in (manifest.get("workflows") or {}).items():
            if not isinstance(entry, dict):
                continue
            central = entry.get("central_workflow")
            if central in CURATED_RENAMES:
                entry["central_workflow"] = CURATED_RENAMES[str(central)]
                entry["binding"] = "curated"
                entry.pop("catalog", None)
                entry.pop("catalog_hash", None)
                entry.pop("shared_variant", None)
                entry.pop("implementation_sha256", None)
                entry["updated_at"] = now_iso()
                changed = True
                binding_count += 1
            elif central in legacy_glee_paths:
                entry["status"] = "blocked"
                entry["blockers"] = [
                    "legacy Glee executor disabled: Glee is only the canonical repoless Jules API audit that updates one PR comment"
                ]
                for key in (
                    "central_workflow",
                    "catalog",
                    "catalog_hash",
                    "binding",
                    "shared_variant",
                    "implementation_sha256",
                ):
                    entry.pop(key, None)
                entry["updated_at"] = now_iso()
                changed = True
                blocked_legacy += 1
            elif central in old_to_new:
                new_path, variant = old_to_new[str(central)]
                implementation_hash = str(entry.get("catalog_hash") or "")
                entry["central_workflow"] = new_path
                entry["binding"] = "shared-variant"
                entry["shared_variant"] = variant
                if implementation_hash:
                    entry["implementation_sha256"] = implementation_hash
                entry.pop("catalog", None)
                entry.pop("catalog_hash", None)
                entry["updated_at"] = now_iso()
                changed = True
                binding_count += 1

        if changed:
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            changed_manifests += 1

    # Remove every old catalog-prefixed workflow after all bindings are rewritten.
    removed = 0
    for path in sorted(WORKFLOWS.glob("catalog-*.y*ml")):
        path.unlink()
        removed += 1

    patch_core()
    patch_dispatch_workflow()
    patch_validator_paths()

    # Post-migration invariants.
    leftovers = sorted(path.name for path in WORKFLOWS.glob("catalog-*.y*ml"))
    if leftovers:
        raise RuntimeError(f"catalog-prefixed workflows remain: {leftovers}")
    hash_named = sorted(
        path.name
        for path in WORKFLOWS.glob("*.y*ml")
        if re.search(r"-[0-9a-f]{16}\.ya?ml$", path.name)
    )
    if hash_named:
        raise RuntimeError(f"hash-suffixed workflow filenames remain: {hash_named}")

    existing = {rel(path) for path in WORKFLOWS.glob("*.y*ml")}
    broken_refs: list[str] = []
    for manifest_path in sorted(REGISTRY.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for source_path, entry in (manifest.get("workflows") or {}).items():
            if not isinstance(entry, dict) or entry.get("status") != "active":
                continue
            central = entry.get("central_workflow")
            if central and central not in existing:
                broken_refs.append(f"{manifest_path}:{source_path}->{central}")
    if broken_refs:
        raise RuntimeError("active manifest references missing workflows:\n" + "\n".join(broken_refs))

    print(f"Removed catalog-prefixed workflow files: {removed}")
    print(f"Created semantic shared workflow families: {len(generated)}")
    print(f"Updated registry manifests: {changed_manifests}")
    print(f"Updated active bindings: {binding_count}")
    print(f"Blocked legacy Glee bindings: {blocked_legacy}")
    print("Curated workflows now use semantic filenames:")
    for old, new in CURATED_RENAMES.items():
        print(f"  {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

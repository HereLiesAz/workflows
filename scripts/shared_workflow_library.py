#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
from pathlib import PurePosixPath
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 4096
_yaml.indent(mapping=2, sequence=4, offset=2)

GENERIC_NAMES = {
    "build",
    "build-and-release",
    "ci",
    "ci-cd",
    "deploy",
    "package",
    "publish",
    "release",
    "test",
    "tests",
    "unit-tests",
}

RESERVED_WORKFLOW_NAMES = {
    "gateway",
    "sync-repository",
    "sync-all-repositories",
    "validate-controller",
}


def load_yaml(text: str) -> Any:
    return _yaml.load(text)


def dump_yaml(data: Any) -> str:
    from io import StringIO

    out = StringIO()
    _yaml.dump(data, out)
    return out.getvalue()


def slugify(value: str) -> str:
    value = re.sub(r"\[shared catalog\]\s*$", "", value, flags=re.IGNORECASE).strip()
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "workflow"


def _technology(text: str) -> str | None:
    checks = (
        ("flutter", ("flutter", "dart")),
        ("android", ("gradle", "android", "assembledebug", "assemblerelease", "bundleRelease".casefold())),
        ("node", ("npm ", "npm\n", "npm@", "pnpm", "yarn", "node-version", "setup-node")),
        ("python", ("pytest", "pip install", "setup-python", "pyproject.toml", "tox")),
        ("docker", ("docker/build-push-action", "docker build", "dockerfile")),
        ("rust", ("cargo ", "rustup", "setup-rust")),
        ("java", ("maven", "mvn ", "setup-java")),
    )
    lowered = text.casefold()
    for name, needles in checks:
        if any(needle.casefold() in lowered for needle in needles):
            return name
    return None


def semantic_family_slug(workflow_name: str, source_path: str, compiled_text: str) -> str:
    """Return the human semantic filename stem for a shared workflow family.

    This deliberately uses behavior/toolchain signals for generic names so that
    unrelated workflows named merely "CI", "Build", or "Release" are not merged.
    Distinct implementations within a true family remain internal variants.
    """

    name_slug = slugify(workflow_name)
    source_slug = slugify(PurePosixPath(source_path).stem)
    lowered = (workflow_name + "\n" + source_path + "\n" + compiled_text).casefold()

    if "glee" in lowered:
        return "legacy-glee"
    if "codeql" in lowered:
        return "codeql"
    if any(token in lowered for token in ("google play", "upload-google-play", "play publish", "publish aab to play", "aab to play")):
        return "google-play"
    if "cloudflare" in lowered or "wrangler" in lowered:
        return "cloudflare-deploy"
    if "vercel" in lowered:
        return "vercel-deploy"
    if "sftp" in lowered:
        return "sftp-deploy"
    if "ftp" in lowered:
        return "ftp-deploy"
    if "deploy-pages" in lowered or "github pages" in lowered:
        return "github-pages"
    if "dependency" in name_slug and any(token in name_slug for token in ("update", "upgrade", "submission")):
        return "dependency-update"
    if "summarize-new-issues" in name_slug or "issue-summary" in name_slug:
        return "issue-summary"
    if "publish-api-reference" in name_slug:
        return "api-reference-publish"
    if "publish-to-github-packages" in name_slug:
        return "github-packages-publish"
    if "maven-central" in name_slug:
        return "maven-central-publish"

    tech = _technology(lowered)
    if name_slug in GENERIC_NAMES:
        return f"{tech}-{name_slug}" if tech else source_slug

    if name_slug in {"android-ci", "android-ci-jules", "android-ci-flutter"}:
        return "flutter-ci" if tech == "flutter" else "android-ci"

    if name_slug.startswith("compile-and-release-apk") or name_slug in {
        "android-release-build",
        "app-release",
        "release-apk",
    }:
        return "android-release"

    if name_slug.startswith("build-publish-aab") or name_slug.startswith("release-aab"):
        return "google-play" if "play" in lowered else "android-release"

    if name_slug in RESERVED_WORKFLOW_NAMES:
        return f"shared-{name_slug}"

    # A descriptive existing name is already the best public family name.
    return name_slug


def shared_workflow_path(workflow_name: str, source_path: str, compiled_text: str) -> str:
    return f".github/workflows/{semantic_family_slug(workflow_name, source_path, compiled_text)}.yml"


def _expression_body(value: Any) -> str:
    text = str(value).strip()
    if text.startswith("${{") and text.endswith("}}"):
        return text[3:-2].strip()
    return text


def _variant_condition(existing: Any, variant: str) -> str:
    variant_expr = f"inputs.shared_variant == '{variant}'"
    if existing is None:
        return "${{ " + variant_expr + " }}"
    return "${{ (" + _expression_body(existing) + ") && (" + variant_expr + ") }}"


def _job_id(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not value or value[0].isdigit():
        value = "job_" + value
    return value


def _rewrite_needs(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, str):
        text = value
        for old, new in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
            text = text.replace(f"needs.{old}.", f"needs.{new}.")
        return text
    if isinstance(value, dict):
        out = CommentedMap()
        for key, item in value.items():
            if key == "needs":
                if isinstance(item, str):
                    out[key] = aliases.get(item, item)
                elif isinstance(item, list):
                    out[key] = CommentedSeq(aliases.get(str(dep), str(dep)) for dep in item)
                else:
                    out[key] = copy.deepcopy(item)
            else:
                out[key] = _rewrite_needs(item, aliases)
        return out
    if isinstance(value, list):
        return CommentedSeq(_rewrite_needs(item, aliases) for item in value)
    return copy.deepcopy(value)


def _merge_mapping(parent: Any, child: Any) -> Any:
    if not isinstance(parent, dict):
        return copy.deepcopy(child)
    if not isinstance(child, dict):
        return copy.deepcopy(parent)
    merged = CommentedMap(copy.deepcopy(parent))
    for key, value in child.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_mapping(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _job_concurrency(value: Any, variant: str) -> Any:
    if value is None:
        return None
    suffix = "-${{ inputs.shared_variant }}"
    if isinstance(value, str):
        return value + suffix
    if isinstance(value, dict):
        out = CommentedMap(copy.deepcopy(value))
        group = out.get("group")
        if group is not None:
            out["group"] = str(group) + suffix
        return out
    return copy.deepcopy(value)


def compiled_variant_jobs(compiled_text: str, variant: str) -> CommentedMap:
    doc = load_yaml(compiled_text)
    if not isinstance(doc, dict):
        raise ValueError("compiled shared workflow is not a mapping")

    allowed_top = {"name", "run-name", "on", "permissions", "env", "defaults", "concurrency", "jobs"}
    unsupported = set(doc) - allowed_top
    if unsupported:
        raise ValueError(f"unsupported top-level keys for shared-family bundling: {sorted(unsupported)}")

    jobs = doc.get("jobs") or {}
    if not isinstance(jobs, dict) or not jobs:
        raise ValueError("compiled shared workflow has no jobs")

    prefix = f"v_{variant}__"
    aliases = {str(job_id): prefix + _job_id(str(job_id)) for job_id in jobs}
    top_permissions = doc.get("permissions")
    top_env = doc.get("env")
    top_defaults = doc.get("defaults")
    top_concurrency = doc.get("concurrency")

    transformed = CommentedMap()
    for old_id, raw_job in jobs.items():
        if not isinstance(raw_job, dict):
            raise ValueError(f"job {old_id!r} is not a mapping")
        job = _rewrite_needs(raw_job, aliases)
        if top_permissions is not None and "permissions" not in job:
            job["permissions"] = copy.deepcopy(top_permissions)
        if top_env is not None:
            job["env"] = _merge_mapping(top_env, job.get("env") or {})
        if top_defaults is not None:
            job["defaults"] = _merge_mapping(top_defaults, job.get("defaults") or {})
        if top_concurrency is not None and "concurrency" not in job:
            job["concurrency"] = _job_concurrency(top_concurrency, variant)
        job["if"] = _variant_condition(job.get("if"), variant)
        transformed[aliases[str(old_id)]] = job
    return transformed


def _dispatch_inputs(doc: dict[str, Any]) -> CommentedMap:
    on_value = doc.get("on") or {}
    if not isinstance(on_value, dict):
        raise ValueError("compiled shared workflow has invalid on mapping")
    dispatch = on_value.get("workflow_dispatch") or {}
    if not isinstance(dispatch, dict):
        raise ValueError("compiled shared workflow is not workflow_dispatch based")
    inputs = dispatch.get("inputs") or {}
    if not isinstance(inputs, dict):
        raise ValueError("compiled shared workflow has invalid dispatch inputs")
    return CommentedMap(copy.deepcopy(inputs))


def _variant_guard_script(variants: list[str]) -> str:
    choices = "|".join(sorted(variants))
    return (
        "set -euo pipefail\n"
        'case "$SHARED_VARIANT" in\n'
        f"  {choices}) ;;\n"
        '  *) echo "Unknown shared workflow variant: $SHARED_VARIANT" >&2; exit 1 ;;\n'
        "esac\n"
    )


def build_shared_family(
    family_slug: str,
    variants: list[tuple[str, str]],
) -> str:
    if not variants:
        raise ValueError("shared workflow family requires at least one variant")

    parsed = [load_yaml(text) for _, text in variants]
    first_inputs = _dispatch_inputs(parsed[0])
    for doc in parsed[1:]:
        other = _dispatch_inputs(doc)
        if dump_yaml(other) != dump_yaml(first_inputs):
            raise ValueError(f"dispatch input shape differs inside family {family_slug}")

    first_inputs["shared_variant"] = CommentedMap({
        "required": True,
        "type": "string",
        "description": "Internal implementation selector from the central registry.",
    })

    variant_ids = [variant for variant, _ in variants]
    jobs = CommentedMap()
    jobs["shared_variant_guard"] = CommentedMap({
        "runs-on": "ubuntu-latest",
        "permissions": CommentedMap({}),
        "env": CommentedMap({"SHARED_VARIANT": "${{ inputs.shared_variant }}"}),
        "steps": CommentedSeq([
            CommentedMap({
                "name": "Validate registered shared workflow variant",
                "shell": "bash",
                "run": _variant_guard_script(variant_ids),
            })
        ]),
    })

    for variant, compiled_text in sorted(variants):
        for job_id, job in compiled_variant_jobs(compiled_text, variant).items():
            if job_id in jobs:
                raise ValueError(f"duplicate bundled job id: {job_id}")
            jobs[job_id] = job

    doc = CommentedMap()
    doc["name"] = "Shared · " + family_slug.replace("-", " ").title()
    doc["run-name"] = "${{ inputs.target_repository }} · ${{ inputs.source_workflow_path }}"
    doc["on"] = CommentedMap({
        "workflow_dispatch": CommentedMap({"inputs": first_inputs})
    })
    doc["jobs"] = jobs

    header = (
        "# Central semantic shared-workflow family.\n"
        "# Public identity is the filename; implementation hashes are internal registry metadata only.\n"
        "# Do not edit generated variant jobs by hand; update the source workflow or synchronizer.\n"
    )
    return header + dump_yaml(doc)


def family_variants(text: str) -> set[str]:
    doc = load_yaml(text)
    jobs = (doc or {}).get("jobs") or {}
    variants: set[str] = set()
    for job_id in jobs:
        match = re.match(r"^v_([0-9a-f]{16})__", str(job_id))
        if match:
            variants.add(match.group(1))
    return variants


def add_shared_variant(existing_text: str | None, family_slug: str, variant: str, compiled_text: str) -> str:
    if existing_text is None:
        return build_shared_family(family_slug, [(variant, compiled_text)])

    existing_doc = load_yaml(existing_text)
    if not isinstance(existing_doc, dict):
        raise ValueError(f"existing shared family {family_slug} is invalid YAML")
    current = family_variants(existing_text)
    if variant in current:
        return existing_text

    # Reconstruct existing variants from the generated family is intentionally
    # avoided: callers adding a new variant must use append_shared_variant so
    # existing job bodies and comments remain untouched.
    return append_shared_variant(existing_text, family_slug, variant, compiled_text)


def append_shared_variant(existing_text: str, family_slug: str, variant: str, compiled_text: str) -> str:
    doc = load_yaml(existing_text)
    if not isinstance(doc, dict):
        raise ValueError(f"existing shared family {family_slug} is invalid")
    jobs = doc.get("jobs") or CommentedMap()
    if variant in family_variants(existing_text):
        return existing_text

    on_value = doc.get("on") or {}
    dispatch = on_value.get("workflow_dispatch") or {}
    existing_inputs = dispatch.get("inputs") or {}
    candidate_inputs = _dispatch_inputs(load_yaml(compiled_text))
    for key in existing_inputs:
        if key == "shared_variant":
            continue
        if key not in candidate_inputs:
            raise ValueError(f"new variant is missing dispatch input {key!r} in family {family_slug}")

    for job_id, job in compiled_variant_jobs(compiled_text, variant).items():
        if job_id in jobs:
            raise ValueError(f"duplicate bundled job id: {job_id}")
        jobs[job_id] = job
    doc["jobs"] = jobs

    variants = sorted(family_variants(dump_yaml(doc)))
    guard = jobs.get("shared_variant_guard")
    if not isinstance(guard, dict):
        raise ValueError(f"family {family_slug} has no shared_variant_guard")
    steps = guard.get("steps") or []
    if not steps or not isinstance(steps[0], dict):
        raise ValueError(f"family {family_slug} guard shape changed")
    steps[0]["run"] = _variant_guard_script(variants)

    header = (
        "# Central semantic shared-workflow family.\n"
        "# Public identity is the filename; implementation hashes are internal registry metadata only.\n"
        "# Do not edit generated variant jobs by hand; update the source workflow or synchronizer.\n"
    )
    return header + dump_yaml(doc)

#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "workflow-policy.json"
WORKFLOW_DIR = ROOT / ".github" / "workflows"

POLICY_HEADER_RE = re.compile(r"(?m)^# workflow-policy:\s*generalized-v1\s*$")
PURPOSE_RE = re.compile(r"(?m)^# workflow-purpose:\s*(\S.*)$")
REQUIRED_SECRET_RE = re.compile(
    r"(?m)^# required-secret:\s*([A-Z][A-Z0-9_]*)\s*\|\s*(\S.*)$"
)
SECRET_REFERENCE_RE = re.compile(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)")
HERELIESAZ_REPOSITORY_RE = re.compile(r"\bHereLiesAz/([A-Za-z0-9_.-]+)")
HERELIESAZ_PACKAGE_RE = re.compile(
    r"\b(?:com|org|io)\.hereliesaz\.[A-Za-z0-9_.-]+",
    re.IGNORECASE,
)


def error(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def workflow_dispatch_inputs(doc: dict[str, Any]) -> dict[str, Any]:
    on_value = doc.get("on")
    if not isinstance(on_value, dict):
        return {}
    dispatch = on_value.get("workflow_dispatch")
    if not isinstance(dispatch, dict):
        return {}
    inputs = dispatch.get("inputs")
    return inputs if isinstance(inputs, dict) else {}


def step_runs(job: dict[str, Any]) -> str:
    values: list[str] = []
    for step in job.get("steps") or []:
        if isinstance(step, dict) and isinstance(step.get("run"), str):
            values.append(step["run"])
    return "\n".join(values)


def repository_bound_workflows() -> set[str]:
    """Return generated executor paths owned by active repository bindings.

    These workflows are emitted by the repository synchronizer and validated by the
    collection audit's binding/namespace checks. The generalized-v1 contract applies
    to hand-authored reusable central workflows, not generated repository executors.
    """
    paths: set[str] = set()
    registry_root = ROOT / "registry"
    if not registry_root.is_dir():
        return paths

    for manifest_path in registry_root.glob("*/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in (manifest.get("workflows") or {}).values():
            if not isinstance(entry, dict):
                continue
            if entry.get("status") != "active" or entry.get("binding") != "repository":
                continue
            central_workflow = str(entry.get("central_workflow") or "").strip()
            if central_workflow:
                paths.add(central_workflow)
    return paths


def validate_new_workflow(
    path: Path,
    text: str,
    secret_catalog: dict[str, Any],
    errors: list[str],
) -> None:
    if not POLICY_HEADER_RE.search(text):
        error(errors, path, "new workflow is missing '# workflow-policy: generalized-v1'")
        return

    purpose_match = PURPOSE_RE.search(text)
    if not purpose_match or not purpose_match.group(1).strip():
        error(errors, path, "new workflow must declare '# workflow-purpose: ...'")

    declared_pairs = REQUIRED_SECRET_RE.findall(text)
    declared: dict[str, str] = {}
    for name, purpose in declared_pairs:
        if name in declared:
            error(errors, path, f"required secret {name} is declared more than once")
        declared[name] = purpose.strip()

    referenced = set(SECRET_REFERENCE_RE.findall(text))
    undeclared = sorted(referenced - set(declared))
    if undeclared:
        error(
            errors,
            path,
            "secret reference(s) lack '# required-secret: NAME | purpose': "
            + ", ".join(undeclared),
        )

    unused = sorted(set(declared) - referenced)
    if unused:
        error(
            errors,
            path,
            "declared required secret(s) are not referenced by the workflow: "
            + ", ".join(unused),
        )

    for name, purpose in declared.items():
        catalog_entry = secret_catalog.get(name)
        if not isinstance(catalog_entry, dict):
            error(
                errors,
                path,
                f"{name} is not in the existing secret catalog; add it to "
                "policy/workflow-policy.json with an explicit purpose only if no existing "
                "secret satisfies the requirement",
            )
            continue
        catalog_purpose = str(catalog_entry.get("purpose") or "").strip()
        if not catalog_purpose:
            error(errors, path, f"secret catalog entry {name} has no purpose")
        if len(purpose) < 12:
            error(errors, path, f"required secret {name} needs a plain-language purpose")

    literal_repositories = {
        match.group(1)
        for match in HERELIESAZ_REPOSITORY_RE.finditer(text)
        if match.group(1).casefold() != "workflows"
    }
    if literal_repositories:
        error(
            errors,
            path,
            "hard-codes target HereLiesAz repository name(s): "
            + ", ".join(sorted(literal_repositories)),
        )

    packages = sorted(set(HERELIESAZ_PACKAGE_RE.findall(text)))
    if packages:
        error(
            errors,
            path,
            "hard-codes HereLiesAz package/application identifier(s): " + ", ".join(packages),
        )

    yaml = YAML(typ="safe")
    try:
        doc = yaml.load(text)
    except Exception as exc:
        error(errors, path, f"invalid YAML: {exc}")
        return
    if not isinstance(doc, dict):
        error(errors, path, "workflow must be a YAML mapping")
        return

    inputs = workflow_dispatch_inputs(doc)
    target = inputs.get("target_repository")
    if not isinstance(target, dict) or target.get("required") is not True:
        error(
            errors,
            path,
            "generalized workflow must expose required workflow_dispatch input "
            "'target_repository'",
        )

    jobs = doc.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        error(errors, path, "workflow must contain jobs")
        return

    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            uses = str(step.get("uses") or "")
            if not uses.startswith("actions/checkout@"):
                continue
            with_values = step.get("with") or {}
            if not isinstance(with_values, dict):
                continue
            repository = with_values.get("repository")
            if repository is None:
                continue
            repository_text = str(repository)
            if "inputs.target_repository" not in repository_text:
                error(
                    errors,
                    path,
                    f"job {job_id!r} checks out a literal/non-generalized repository: "
                    f"{repository_text!r}",
                )

    if declared:
        preflight = jobs.get("policy_secret_preflight")
        if not isinstance(preflight, dict):
            error(
                errors,
                path,
                "workflows with required secrets must define job 'policy_secret_preflight'",
            )
            return
        env = preflight.get("env") or {}
        if not isinstance(env, dict):
            env = {}
        runs = step_runs(preflight)
        for name, purpose in declared.items():
            expected_ref = f"secrets.{name}"
            if not any(expected_ref in str(value) for value in env.values()):
                error(
                    errors,
                    path,
                    f"policy_secret_preflight does not map required secret {name}",
                )
            if f"Missing required secret {name}" not in runs:
                error(
                    errors,
                    path,
                    f"policy_secret_preflight does not explicitly report missing {name}",
                )
            if purpose not in runs:
                error(
                    errors,
                    path,
                    f"policy_secret_preflight missing purpose text for {name}: {purpose}",
                )



def validation_errors_for_workflow(workflow_path: str) -> list[str]:
    """Return policy violations for one central workflow path.

    Grandfathered paths are valid by definition. This function is also used by
    runtime dispatch so direct pushes cannot bypass the admission policy.
    """

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    grandfathered = set(policy.get("grandfathered_workflows") or [])
    if workflow_path in grandfathered or workflow_path in repository_bound_workflows():
        return []

    path = ROOT / workflow_path
    if not path.is_file():
        return [f"{workflow_path}: central workflow file is missing"]

    secret_catalog = policy.get("secret_catalog") or {}
    errors: list[str] = []
    if not isinstance(secret_catalog, dict):
        return ["policy/workflow-policy.json: secret_catalog must be an object"]

    validate_new_workflow(
        path,
        path.read_text(encoding="utf-8"),
        secret_catalog,
        errors,
    )
    return errors


def main() -> int:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    grandfathered = set(policy.get("grandfathered_workflows") or [])
    generated_repository_workflows = repository_bound_workflows()
    secret_catalog = policy.get("secret_catalog") or {}
    errors: list[str] = []

    if not isinstance(secret_catalog, dict):
        raise RuntimeError("policy secret_catalog must be an object")

    for name, entry in sorted(secret_catalog.items()):
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", str(name)):
            errors.append(f"policy/workflow-policy.json: invalid secret name {name!r}")
        if not isinstance(entry, dict) or not str(entry.get("purpose") or "").strip():
            errors.append(
                f"policy/workflow-policy.json: secret {name!r} must have an explicit purpose"
            )

    current = {
        path.relative_to(ROOT).as_posix()
        for path in WORKFLOW_DIR.glob("*.y*ml")
        if path.is_file()
    }

    policy_governed = current - grandfathered - generated_repository_workflows
    for workflow_path in sorted(policy_governed):
        path = ROOT / workflow_path
        validate_new_workflow(
            path,
            path.read_text(encoding="utf-8"),
            secret_catalog,
            errors,
        )

    if errors:
        for item in errors:
            print(f"ERROR: {item}")
        print(f"generalized workflow policy failed with {len(errors)} error(s)")
        return 1

    print(
        "generalized workflow policy passed: "
        f"{len(grandfathered & current)} grandfathered, "
        f"{len(generated_repository_workflows & current)} generated repository executor(s), "
        f"{len(policy_governed)} policy-governed new workflow(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

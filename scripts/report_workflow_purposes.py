#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
_yaml = YAML(typ="safe")


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(key)
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def source_behavior(doc: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    chunks: list[str] = []
    uses: list[str] = []
    step_names: list[str] = []
    for job_id, job in (doc.get("jobs") or {}).items():
        chunks.append(str(job_id))
        if not isinstance(job, dict):
            continue
        if job.get("name"):
            chunks.append(str(job["name"]))
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            name = str(step.get("name") or "").strip()
            action = str(step.get("uses") or "").strip()
            run = str(step.get("run") or "")
            if name:
                step_names.append(name)
                chunks.append(name)
            if action:
                uses.append(action)
                chunks.append(action)
            if run:
                chunks.append(run)
        for value in (job.get("environment"), job.get("container"), job.get("services")):
            chunks.extend(iter_strings(value))
    return "\n".join(chunks).casefold(), sorted(set(uses)), step_names


def trigger_kinds(doc: dict[str, Any]) -> list[str]:
    on_value = doc.get("on")
    if isinstance(on_value, str):
        return [on_value]
    if isinstance(on_value, list):
        return sorted(str(item) for item in on_value)
    if isinstance(on_value, dict):
        return sorted(str(key) for key in on_value)
    return []


def effects_for(text: str, uses: list[str], name: str, path: str) -> set[str]:
    all_text = "\n".join([text, name.casefold(), path.casefold(), "\n".join(uses).casefold()])
    effects: set[str] = set()

    def has(*terms: str) -> bool:
        return any(term.casefold() in all_text for term in terms)

    # Distribution / deployment destinations.
    if has("signazp", "sign released .azp assets", "azp_private_key"):
        effects.add("azp-sign")
    if has("model_url", "fetch upstream model") and has("manifest.json", "*.azp", "pack .azp"):
        effects.add("azp-model-release")
    if has("gh release ", "softprops/action-gh-release", "ncipollo/release-action", "sangatdesai/release-apk", "release create", "release upload"):
        effects.add("github-release")
    if has("upload-google-play", "gradle-play-publisher", "publishbundle", "publishapk", "play_multitrack_publish.py", "publish_play.py", "androidpublisher", "edits().bundles"):
        effects.add("google-play")
    if has("npm publish", "pnpm publish", "yarn npm publish", "changesets/action", "pnpm run release", "publish-one-retry.sh", "publish-staged.sh"):
        effects.add("npm-publish")
    if has("publishplugin", "gradle plugin portal", "plugins.gradle.org"):
        effects.add("gradle-plugin-publish")
    if has("publishallpublication", "publishtomaven", "maven central", "sonatype", "./gradlew publish"):
        effects.add("maven-publish")
    if has("actions/deploy-pages", "upload-pages-artifact", "github-pages"):
        effects.add("pages-deploy")
    if has("sftp", "ftp-deploy", "scp-action", "rsync ", "ssh-deploy", "lftp"):
        effects.add("file-server-deploy")
    if has("huggingface", "hf upload", "huggingface-cli"):
        if has("space", "spaces"):
            effects.add("huggingface-space-deploy")
        else:
            effects.add("huggingface-publish")
    if has("docker/build-push-action", "docker push", "ghcr.io", "docker/login-action"):
        effects.add("container-publish")
    if has("docker build ", "docker build."):
        effects.add("container-build")
    if has("vercel deploy", "vercel --prod", "vercel-action", "deploy-storefront", "vercel_project_id", "vercel_org_id"):
        effects.add("vercel-deploy")

    # Build products.
    if has("assemble", "bundlerelease", "bundle release", "gradlew bundle", "gradlew assemble") and has("gradle", "gradlew"):
        effects.add("android-build")
    if has("jpackage", "packagedmg", "packagemsi", "packagedeb", "packagerpm", "packagedistributionforcurrentos", "compose.desktop", "electron-builder", "desktop build", "desktop-build"):
        effects.add("desktop-build")
    if has("pyinstaller"):
        effects.add("python-executable")
    if has("actions/upload-artifact", "artifact upload"):
        effects.add("artifact-upload")

    # Verification / analysis.
    if has("github/codeql-action/init", "github/codeql-action/analyze"):
        effects.add("codeql")
    if has("github/codeql-action/upload-sarif"):
        effects.add("sarif-upload")
    if has("./gradlew test", "gradle test", "pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test"):
        effects.add("tests")
    if has("./gradlew lint", "detekt", "ktlint", "eslint", "ruff ", "pylint", "cargo clippy", "shellcheck"):
        effects.add("lint")
    if has("dependency-review-action"):
        effects.add("dependency-review")

    # Repository automation / maintenance.
    if has("clear gradle cache", ".gradle/caches", "clear_cache", "clear-cache"):
        effects.add("cache-clear")
    if has("update dependencies", "update-libs", "dependencyupdates", "versionsplugin", "renovate"):
        effects.add("dependency-update")
    if has("actions/labeler", "labeler"):
        effects.add("labeling")
    if has("visibility", "private=true", "private=false", "repos/${", "repo visibility"):
        effects.add("repository-visibility")
    if has("sync embedded guide", "sync-embedded-guide", "embedded guide"):
        effects.add("docs-sync")
    if has("vendor artifact", "vendor-artifact", "chatgpt vendor"):
        effects.add("vendor-artifact")
    if has("backup", "git bundle", "context backup"):
        effects.add("backup")
    if has("summarize new issues", "issue summary", "summarize issue", "summary.yml"):
        effects.add("issue-summary")
    if has("actions/stale", "mark stale issues", "stale-pr-message", "stale-issue-message"):
        effects.add("stale-maintenance")
    if has("dokkageneratemarkdown", "dokka") and has("wiki", "api-reference"):
        effects.add("docs-wiki-publish")
    if has("wasmjsbrowserdistribution", "wasm distribution"):
        effects.add("wasm-build")

    # Jules/Glee are separate behaviors even though several use the same APIs.
    if has("glee audit", "jules-glee"):
        effects.add("glee-audit")
    if has("jules auto-merge", "jules-auto-merge"):
        effects.add("jules-auto-merge")
    if has("jules agent", "jules-agent"):
        effects.add("jules-agent")
    if has("jules dispatch", "jules-dispatch"):
        effects.add("jules-dispatch")

    return effects


def purpose_for(effects: set[str], name: str, path: str) -> str:
    # Purpose is based on the externally visible result, not implementation details.
    # Some workflows intentionally share mechanisms (SFTP, repository writes, Hugging Face)
    # while accomplishing different things. Keep those semantic distinctions explicit so the
    # audit never calls them duplicates merely because the transport is the same.
    hint = f"{name} {path}".casefold()

    # Manually reviewed repository-bound and agent workflows. These labels record
    # semantic intent even when execution must remain local because an action is
    # coupled to the runner repository or the workflow is genuinely project-specific.
    reviewed_hints = (
        ("jules scheduled issue triage", "jules-issue-triage"),
        ("jules invoke", "jules-task-dispatch"),
        ("jules security fixer", "jules-security-remediation"),
        ("assign jules to issues", "jules-issue-automation"),
        ("jules issue handler", "jules-issue-automation"),
        ("jules branch pr handler", "jules-branch-automation"),
        ("jules branch handler", "jules-branch-automation"),
        ("antigravity scheduled issue triage", "antigravity-issue-triage"),
        ("antigravity dispatch", "antigravity-task-dispatch"),
        ("gemini scheduled issue triage", "gemini-issue-triage"),
        ("gemini dispatch", "gemini-task-dispatch"),
        ("enforce contribution guidelines", "contribution-guideline-review"),
        ("dependency submission", "dependency-graph-submission"),
        ("dependency graph", "dependency-graph-submission"),
        ("java ci with gradle", "java-gradle-ci-and-dependency-submission"),
        ("distributed compute", "distributed-compute-ci"),
        ("inspect epoch-8 memory artifacts", "model-artifact-inspection"),
        ("live runtime verification", "live-runtime-verification"),
        ("deduplicate data", "data-deduplication"),
        ("enrich bar data", "data-enrichment"),
        ("the nag bot", "issue-reminder-automation"),
        ("materialize animation boundaries", "animation-boundary-materialization"),
        ("render prop id", "prop-id-rendering"),
        ("verify real storefront checkout", "storefront-integration-verification"),
        ("terrarium ci", "terrarium-ci"),
        ("legacy glee pr review", "legacy-pull-request-audit"),
    )
    for reviewed_hint, purpose in reviewed_hints:
        if reviewed_hint in hint:
            return purpose
    if "registry-sync" in hint or "sync registry from extension repos" in hint:
        return "registry-catalog-sync"
    if "vercel-logs" in hint or "vercel build logs" in hint:
        return "vercel-build-log-diagnostic"
    if "apply-unattached-visibility" in hint or "apply unattached overflow and visibility" in hint:
        return "unattached-visibility-migration"
    if "sync-platform-parity" in hint or "sync platform parity" in hint:
        return "platform-parity-sync"
    if "deploy-docs-sftp" in hint or "deploy docs over ftp" in hint:
        return "documentation-file-server-deploy"
    if "mirror-models" in hint or "mirror models to hf" in hint:
        return "huggingface-model-mirror"
    if "remove_painting" in hint or "remove painting" in hint:
        return "painting-removal"
    if "theater_bake" in hint or "theater bake" in hint:
        return "theater-bake"
    if "generate-wrapper" in hint or "generate gradle wrapper" in hint:
        return "gradle-wrapper-generation"
    if "android-ci" in hint and not effects:
        return "android-ci"
    if "provision-storage" in hint or "provision durable storage" in hint:
        return "package-storage-provision"
    if "submissions" in hint:
        return "package-submissions"
    if "bump-more-from-az" in hint or "bake more-from-az" in hint:
        return "app-catalog-bake"
    if "bootstrap art" in hint or path.endswith("/bootstrap.yml"):
        return "art-data-bootstrap"
    if "paperplanes wizard pipeline" in hint or path.endswith("/pipeline.yml"):
        return "ai-media-pipeline"
    if "azp-sign" in effects:
        return "azp-sign-release"
    if "azp-model-release" in effects:
        return "azp-model-release"
    if "glee-audit" in effects:
        return "pull-request-audit"
    if "jules-auto-merge" in effects:
        return "jules-branch-auto-merge"
    if "jules-agent" in effects:
        return "jules-agent"
    if "jules-dispatch" in effects:
        return "jules-task-dispatch"
    if "stale-maintenance" in effects:
        return "stale-issue-maintenance"
    if "docs-wiki-publish" in effects:
        return "documentation-wiki-publish"
    if "container-build" in effects and "container-publish" not in effects:
        return "container-build"
    if "vercel-deploy" in effects:
        return "vercel-deploy"
    if "wasm-build" in effects:
        return "wasm-ci"
    if "google-play" in effects and "github-release" in effects:
        return "android-multichannel-release"
    if "github-release" in effects and "android-build" in effects and "desktop-build" in effects:
        return "multi-platform-app-release"
    if "github-release" in effects and "android-build" in effects and "python-executable" in effects:
        return "multi-target-app-release"
    if "google-play" in effects:
        return "android-publish-google-play"
    if "github-release" in effects and "android-build" in effects:
        return "android-build-and-github-release"
    if "github-release" in effects and "desktop-build" in effects:
        return "desktop-build-and-github-release"
    if "github-release" in effects:
        return "github-release"
    if "npm-publish" in effects:
        return "npm-publish"
    if "gradle-plugin-publish" in effects:
        return "gradle-plugin-publish"
    if "maven-publish" in effects:
        return "maven-publish"
    if "pages-deploy" in effects:
        return "github-pages-deploy"
    if "file-server-deploy" in effects:
        return "file-server-deploy"
    if "huggingface-space-deploy" in effects:
        return "huggingface-space-deploy"
    if "huggingface-publish" in effects:
        return "huggingface-publish"
    if "container-publish" in effects:
        return "container-publish"
    if "codeql" in effects:
        return "code-security-scan"
    if "sarif-upload" in effects:
        return "static-analysis-sarif"
    if "dependency-review" in effects:
        return "dependency-security-review"
    if "dependency-update" in effects:
        return "dependency-update"
    if "cache-clear" in effects:
        return "build-cache-clear"
    if "repository-visibility" in effects:
        return "repository-visibility-policy"
    if "docs-sync" in effects:
        return "documentation-sync"
    if "vendor-artifact" in effects:
        return "vendor-artifact-build"
    if "issue-summary" in effects:
        return "issue-summary"
    if "labeling" in effects:
        return "pull-request-labeling"
    if "backup" in effects:
        return "repository-backup"
    if "desktop-build" in effects:
        return "desktop-build"
    if "android-build" in effects and ("tests" in effects or "lint" in effects):
        return "android-ci"
    if "android-build" in effects:
        return "android-build"
    if "tests" in effects or "lint" in effects:
        return "ci-validation"
    if "artifact-upload" in effects:
        return "artifact-build"

    # Last-resort semantic hints for workflows whose shell is mostly delegated.
    if "summary" in hint and "issue" in hint:
        return "issue-summary"
    if "deploy" in hint:
        return "deployment-other"
    if "release" in hint:
        return "release-other"
    if "build" in hint:
        return "build-other"
    if "update" in hint:
        return "maintenance-update"
    if "sync" in hint:
        return "synchronization"
    return "needs-manual-review"


def load_source(entry: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    rel = str(entry.get("registry_source") or "")
    if not rel:
        return None, "missing registry_source"
    path = ROOT / rel
    if not path.exists():
        return None, f"missing source file {rel}"
    try:
        doc = _yaml.load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"invalid YAML in {rel}: {exc}"
    if not isinstance(doc, dict):
        return None, f"source {rel} is not a mapping"
    return doc, None


def build_report() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    status_counts: Counter[str] = Counter()

    for manifest_path in sorted(REGISTRY.glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{manifest_path.relative_to(ROOT)}: {exc}")
            continue
        repository = str((manifest.get("repository") or {}).get("full_name") or "")
        for source_path, entry in sorted((manifest.get("workflows") or {}).items()):
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status") or "unknown")
            status_counts[status] += 1
            if status not in {"active", "local", "blocked"}:
                continue
            doc, error = load_source(entry)
            if error or doc is None:
                errors.append(f"{repository}:{source_path}: {error}")
                continue
            name = str(entry.get("name") or doc.get("name") or source_path)
            behavior_text, uses, step_names = source_behavior(doc)
            effects = effects_for(behavior_text, uses, name, source_path)
            purpose = purpose_for(effects, name, source_path)
            central_workflow = str(entry.get("central_workflow") or "")
            rows.append({
                "repository": repository,
                "source_path": source_path,
                "name": name,
                "status": status,
                "binding": str(entry.get("binding") or ""),
                "central_workflow": central_workflow,
                "registry_source": str(entry.get("registry_source") or ""),
                "source_sha256": str(entry.get("source_sha256") or ""),
                "triggers": trigger_kinds(doc),
                "purpose": purpose,
                "effects": sorted(effects),
                "uses": uses,
                "step_names": step_names,
            })

    by_purpose: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_repo_purpose: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_purpose[row["purpose"]].append(row)
        by_repo_purpose[(row["repository"], row["purpose"])].append(row)

    groups = []
    for purpose, members in sorted(by_purpose.items(), key=lambda item: (-len(item[1]), item[0])):
        groups.append({
            "purpose": purpose,
            "count": len(members),
            "repositories": sorted({m["repository"] for m in members}),
            "names": sorted({m["name"] for m in members}),
            "source_paths": sorted({m["source_path"] for m in members}),
            "distinct_source_hashes": len({m["source_sha256"] for m in members}),
            "bindings": dict(sorted(Counter(m["binding"] for m in members).items())),
            "effects": sorted({effect for m in members for effect in m["effects"]}),
        })

    intra_repo = []
    for (repo, purpose), members in sorted(by_repo_purpose.items()):
        if len(members) < 2:
            continue
        intra_repo.append({
            "repository": repo,
            "purpose": purpose,
            "count": len(members),
            "workflows": [
                {"source_path": m["source_path"], "name": m["name"], "source_sha256": m["source_sha256"], "effects": m["effects"]}
                for m in members
            ],
        })

    return {
        "summary": {
            "manifest_count": len(list(REGISTRY.glob("*/manifest.json"))),
            "workflow_entries_by_status": dict(sorted(status_counts.items())),
            "active_workflows": sum(1 for row in rows if row["status"] == "active"),
            "live_workflows": len(rows),
            "local_workflows": sum(1 for row in rows if row["status"] == "local"),
            "blocked_workflows": sum(1 for row in rows if row["status"] == "blocked"),
            "purpose_groups": len(groups),
            "needs_manual_review": sum(1 for row in rows if row["purpose"] == "needs-manual-review"),
            "same_repository_same_purpose_groups": len(intra_repo),
        },
        "groups": groups,
        "same_repository_same_purpose": intra_repo,
        "manual_review": [row for row in rows if row["purpose"] == "needs-manual-review"],
        "workflows": rows,
        "errors": errors,
    }


def markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Workflow purpose audit",
        "",
        "This report groups active workflows by **what they accomplish**, not by filename, repository, or implementation hash.",
        "",
        f"- Active centralized workflows: **{summary['active_workflows']}**",
        f"- Live workflows audited: **{summary['live_workflows']}** (including {summary['local_workflows']} local and {summary['blocked_workflows']} blocked)",
        f"- Purpose groups: **{summary['purpose_groups']}**",
        f"- Manual-review workflows: **{summary['needs_manual_review']}**",
        f"- Same-repository/same-purpose groups: **{summary['same_repository_same_purpose_groups']}**",
        "",
        "## Purpose groups",
        "",
        "| Purpose | Workflows | Repositories | Source variants | Effects |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for group in report["groups"]:
        effects = ", ".join(group["effects"]) or "—"
        lines.append(f"| `{group['purpose']}` | {group['count']} | {len(group['repositories'])} | {group['distinct_source_hashes']} | {effects} |")

    lines.extend(["", "## Same repository, same purpose", ""])
    if not report["same_repository_same_purpose"]:
        lines.append("None.")
    else:
        for item in report["same_repository_same_purpose"]:
            lines.append(f"### {item['repository']} — `{item['purpose']}`")
            for workflow in item["workflows"]:
                lines.append(f"- `{workflow['source_path']}` — {workflow['name']}")
            lines.append("")

    lines.extend(["", "## Manual review", ""])
    if not report["manual_review"]:
        lines.append("None.")
    else:
        for row in report["manual_review"]:
            lines.append(f"- `{row['repository']}:{row['source_path']}` — {row['name']}")

    lines.extend(["", "## Errors", ""])
    if report["errors"]:
        lines.extend(f"- {error}" for error in report["errors"])
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="workflow-purpose-audit.json")
    parser.add_argument("--markdown", default="workflow-purpose-audit.md")
    args = parser.parse_args()

    report = build_report()
    Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.markdown).write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    for group in report["groups"]:
        print(f"{group['count']:4d}  {len(group['repositories']):4d} repos  {group['distinct_source_hashes']:3d} variants  {group['purpose']}")
    if report["errors"]:
        print(f"warning: {len(report['errors'])} source-loading error(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.parse

import sync_repository_catalog as core
from sync_repository_catalog import *  # noqa: F401,F403


def _load_policy(gh: GitHub, repo_id: int) -> dict:
    try:
        text, _ = gh.get_file(CENTRAL_REPOSITORY, f"registry/{repo_id}/policy.json")
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except ApiError as exc:
        if "-> 404:" in str(exc):
            return {}
        raise


def _apply_disabled_workflows(gh: GitHub, repo: dict, policy: dict, dry_run: bool) -> list[dict]:
    results = []
    disabled = policy.get("disabled_workflows") or []
    if not isinstance(disabled, list):
        raise RuntimeError("policy disabled_workflows must be a list")

    for path in disabled:
        path = str(path)
        try:
            item = gh.contents(repo["full_name"], path)
        except ApiError as exc:
            if "-> 404:" in str(exc):
                continue
            raise
        if not isinstance(item, dict) or item.get("type") != "file":
            continue
        results.append({"path": path, "status": "would-delete" if dry_run else "deleted"})
        if dry_run:
            continue
        quoted = urllib.parse.quote(path, safe="/")
        gh.json(
            "DELETE",
            f"/repos/{repo['full_name']}/contents/{quoted}",
            {
                "message": f"Remove disabled workflow {path}",
                "sha": item["sha"],
                "branch": repo["default_branch"],
            },
        )
    return results


def sync_repository(gh: GitHub, full_name: str, worker_url: str, dry_run: bool = False) -> dict:
    repo = gh.repo(full_name)
    policy = _load_policy(gh, int(repo["id"]))
    policy_cleanup = _apply_disabled_workflows(gh, repo, policy, dry_run)
    result = core.sync_repository(gh, full_name, worker_url, dry_run)

    disabled = {str(path) for path in (policy.get("disabled_workflows") or [])}
    if disabled and not dry_run:
        manifest = core.load_manifest(gh, int(repo["id"]))
        workflows = manifest.get("workflows") or {}
        changed = False
        for path in disabled:
            if path in workflows:
                del workflows[path]
                changed = True
        if changed:
            manifest["workflows"] = workflows
            gh.put_file(
                CENTRAL_REPOSITORY,
                core.manifest_path(int(repo["id"])),
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                f"Apply workflow policy for {repo['full_name']}",
                branch="main",
            )

    result["policy_cleanup"] = policy_cleanup
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind target workflows to the shared HereLiesAz/workflows catalog.")
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

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.parse

try:
    from . import sync_repository as sync
    from . import sync_repository_catalog as core
except ImportError:
    import sync_repository as sync
    import sync_repository_catalog as core


# Repository-specific curated bindings that must survive future controller syncs.
# Keep these here instead of the global path-only catalog map so another repository
# cannot accidentally claim a target-specific executor merely by using the same path.
REPOSITORY_CATALOG_OVERRIDES = {
    "hereliesaz/morphont": {
        ".github/workflows/morphont-publish.yml": ".github/workflows/morphont-publish.yml",
    },
}


class IdempotentGitHub(core.GitHub):
    """GitHub client that avoids write calls when the desired state already exists."""

    def put_file(
        self,
        full_name: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
    ) -> None:
        quoted = urllib.parse.quote(path, safe="/")
        existing_sha = None
        try:
            item = self.contents(full_name, path, ref=branch)
            if isinstance(item, dict):
                existing_sha = item.get("sha")
                encoded = item.get("content")
                if item.get("encoding") == "base64" and isinstance(encoded, str):
                    try:
                        existing = base64.b64decode(encoded).decode()
                    except Exception:
                        existing = None
                    if existing == content:
                        return
        except core.ApiError as exc:
            if "-> 404:" not in str(exc):
                raise

        body: dict[str, object] = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        if existing_sha:
            body["sha"] = existing_sha
        if branch:
            body["branch"] = branch
        self.json("PUT", f"/repos/{full_name}/contents/{quoted}", body)

    def upsert_variable(self, full_name: str, name: str, value: str) -> None:
        quoted = urllib.parse.quote(name, safe="")
        try:
            current = self.json("GET", f"/repos/{full_name}/actions/variables/{quoted}")
            if isinstance(current, dict) and str(current.get("value", "")) == value:
                return
            self.json(
                "PATCH",
                f"/repos/{full_name}/actions/variables/{quoted}",
                {"name": name, "value": value},
            )
        except core.ApiError as exc:
            if "-> 404:" not in str(exc):
                raise
            self.json(
                "POST",
                f"/repos/{full_name}/actions/variables",
                {"name": name, "value": value},
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retry one repository sync while skipping writes that are already in the desired state."
    )
    parser.add_argument("--repository", required=True, help="owner/repository")
    parser.add_argument("--worker-url", default=os.environ.get("WORKER_URL", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    for path, central_workflow in REPOSITORY_CATALOG_OVERRIDES.get(args.repository.casefold(), {}).items():
        core.CATALOG_PATH_OVERRIDES[path] = central_workflow

    gh = IdempotentGitHub(os.environ.get("GH_TOKEN", ""))
    result = sync.sync_repository(gh, args.repository, args.worker_url, args.dry_run)
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

REPOSITORY_CATALOG_OVERRIDES = {
    "hereliesaz/morphont": {
        ".github/workflows/morphont-publish.yml": ".github/workflows/morphont-publish.yml",
    },
}

_base_compact_event_script = sync._compact_event_script


def _compact_event_script(source_path: str, source_text: str) -> str | None:
    compact = _base_compact_event_script(source_path, source_text)
    if compact is not None:
        return compact
    return r'''DISPATCH_EVENT_JSON="$(jq -c '
  def strip_noise:
    if type == "object" then
      with_entries(
        select(.key as $k | [
          "url", "html_url", "avatar_url", "followers_url", "following_url",
          "gists_url", "starred_url", "subscriptions_url", "organizations_url",
          "repos_url", "events_url", "received_events_url", "node_id", "_links"
        ] | index($k) | not)
      ) | map_values(strip_noise)
    elif type == "array" then map(strip_noise)
    else . end;
  strip_noise
' <<<"$EVENT_JSON")"
'''


sync._compact_event_script = _compact_event_script


class IdempotentGitHub(core.GitHub):
    def __init__(self, token: str):
        super().__init__(token)
        self.central_sync_branch = os.environ.get("CENTRAL_SYNC_BRANCH", "").strip()

    def _central_ref(self, full_name: str, ref: str | None) -> str | None:
        if (
            self.central_sync_branch
            and full_name.casefold() == core.CENTRAL_REPOSITORY.casefold()
            and (ref is None or ref == "main")
        ):
            return self.central_sync_branch
        return ref

    def contents(self, full_name: str, path: str, ref: str | None = None):
        return super().contents(full_name, path, ref=self._central_ref(full_name, ref))

    def json(self, method: str, path: str, body=None):
        if (
            self.central_sync_branch
            and method.upper() == "DELETE"
            and path.startswith(f"/repos/{core.CENTRAL_REPOSITORY}/contents/")
            and isinstance(body, dict)
            and body.get("branch") == "main"
        ):
            body = dict(body)
            body["branch"] = self.central_sync_branch
        return super().json(method, path, body)

    def put_file(self, full_name: str, path: str, content: str, message: str, branch: str | None = None) -> None:
        branch = self._central_ref(full_name, branch)
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
            self.json("PATCH", f"/repos/{full_name}/actions/variables/{quoted}", {"name": name, "value": value})
        except core.ApiError as exc:
            if "-> 404:" not in str(exc):
                raise
            self.json("POST", f"/repos/{full_name}/actions/variables", {"name": name, "value": value})


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize one repository while skipping no-op writes.")
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

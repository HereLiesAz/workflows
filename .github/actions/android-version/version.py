#!/usr/bin/env python3
"""The single Android versioning rule (see action.yml). Pure functions are unit-tested in
scripts/test_android_version.py; I/O lives in main()."""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROPERTY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=\s*(.*?)\s*$")


def parse_properties(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if line.lstrip().startswith(("#", "!")):
            continue
        match = PROPERTY_RE.match(line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _int(value: str | None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def recorded_pair(props: dict[str, str]) -> tuple[int, list[int]]:
    """The last published versionCode and versionName fields recorded in the repository."""
    code = _int(props.get("versionCode")) or 0
    name = props.get("versionName", "").strip()
    fields = [_int(part) for part in name.split(".")] if name else []
    if not fields or any(field is None for field in fields):
        fields = [
            _int(props.get("versionMajor")) or 0,
            _int(props.get("versionMinor")) or 0,
            _int(props.get("versionPatch")) or 0,
            _int(props.get("versionBuild")) or 0,
        ]
    return code, [int(field) for field in fields]


def next_pair(props: dict[str, str], play_highest: int) -> tuple[int, str]:
    """versionCode = max(recorded, Play) + 1; versionName = hand-managed major.minor.patch with the
    last field of the previous name + 1."""
    code, fields = recorded_pair(props)
    last = fields[-1] if len(fields) >= 4 else 0
    head = [
        _int(props.get("versionMajor")),
        _int(props.get("versionMinor")),
        _int(props.get("versionPatch")),
    ]
    if any(value is None for value in head):
        head = (fields[:3] + [0, 0, 0])[:3]
    return max(code, play_highest) + 1, ".".join(str(part) for part in [*head, last + 1])


def render_recorded(text: str, code: int, name: str = "") -> str:
    """Set versionCode and, when a name is given, versionName and versionBuild (the name's last
    field); keep every other line. A recorded versionCode is never lowered."""
    current = _int(parse_properties(text).get("versionCode")) or 0
    updates = {"versionCode": str(max(code, current))}
    if name:
        updates.update({"versionName": name, "versionBuild": name.rsplit(".", 1)[-1]})
    out: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        match = PROPERTY_RE.match(line)
        key = match.group(1) if match and not line.lstrip().startswith(("#", "!")) else None
        if key in updates:
            if key not in seen:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
            continue
        out.append(line)
    out.extend(f"{key}={value}" for key, value in updates.items() if key not in seen)
    return "\n".join(out) + "\n"


def play_highest_code(service_account_json: str, package_name: str) -> int:
    """Highest versionCode Play has ever accepted for the package: every uploaded bundle and APK,
    and every release on every track whatever its status."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_json),
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    from googleapiclient.errors import HttpError

    edits = build("androidpublisher", "v3", credentials=credentials, cache_discovery=False).edits()

    def edit_was_deleted(exc: HttpError) -> bool:
        # Play keeps one open edit per app: another run of the same app (its Play publish, or a
        # GitHub release resolving its own code) opening an edit deletes this one mid-read.
        return exc.resp.status == 400 and b"Edit has been deleted" in (exc.content or b"")

    for attempt in range(1, 6):
        try:
            edit_id = edits.insert(packageName=package_name, body={}).execute(num_retries=3)["id"]
        except HttpError as exc:
            # Only "Play has never seen this package" means no code was ever accepted. Every other
            # error propagates: guessing a code here is how apps fell off their sequence.
            if exc.resp.status == 404:
                return 0
            raise
        codes: list[int] = []
        try:
            for bundle in edits.bundles().list(packageName=package_name, editId=edit_id).execute(num_retries=3).get("bundles", []):
                codes.append(int(bundle["versionCode"]))
            for apk in edits.apks().list(packageName=package_name, editId=edit_id).execute(num_retries=3).get("apks", []):
                codes.append(int(apk["versionCode"]))
            for track in edits.tracks().list(packageName=package_name, editId=edit_id).execute(num_retries=3).get("tracks", []):
                for release in track.get("releases", []):
                    codes.extend(int(code) for code in release.get("versionCodes", []))
        except HttpError as exc:
            if not edit_was_deleted(exc) or attempt == 5:
                raise
            print(f"Play edit was replaced by another run; re-reading (attempt {attempt + 1}/5)", file=sys.stderr)
            time.sleep(5 * attempt)
            continue
        try:
            edits.delete(packageName=package_name, editId=edit_id).execute(num_retries=3)
        except HttpError as exc:
            # A read-only edit someone else already replaced needs no cleanup.
            if not edit_was_deleted(exc):
                raise
        return max(codes, default=0)
    raise AssertionError("unreachable")


def github(method: str, url: str, token: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"https://api.github.com{url}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read() or b"{}")


def output(name: str, value: str) -> None:
    print(f"{name}={value}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> int:
    mode = os.environ["MODE"]
    version_file = os.environ.get("VERSION_FILE") or "version.properties"
    if mode == "next":
        path = Path(version_file)
        props = parse_properties(path.read_text(encoding="utf-8")) if path.is_file() else {}
        play = 0
        if os.environ.get("PLAY_SERVICE_ACCOUNT_JSON"):
            package = os.environ.get("PACKAGE_NAME") or ""
            if not package:
                print("::error::package-name is required with service-account-json", file=sys.stderr)
                return 1
            play = play_highest_code(os.environ["PLAY_SERVICE_ACCOUNT_JSON"], package)
        recorded, _ = recorded_pair(props)
        code, name = next_pair(props, play)
        print(f"recorded versionCode={recorded}; highest on Play={play}")
        output("version_code", str(code))
        output("version_name", name)
        return 0
    if mode == "record":
        repository, branch, token = os.environ["RECORD_REPOSITORY"], os.environ["RECORD_BRANCH"], os.environ["GH_TOKEN"]
        code, name = int(os.environ["RECORD_CODE"]), os.environ["RECORD_NAME"]
        url = f"/repos/{repository}/contents/{version_file}"
        # Another release of the same build (Play and GitHub) or a version-contract commit may
        # land between read and write; the contents API then refuses the stale sha. Re-read.
        for attempt in range(1, 9):
            try:
                current = github("GET", f"{url}?ref={branch}", token)
                text, sha = base64.b64decode(current["content"]).decode("utf-8"), current["sha"]
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
                text, sha = "", None
            rendered = render_recorded(text, code, name)
            if rendered == text:
                print(f"{repository}@{branch}:{version_file} already records versionCode {code} or higher")
                return 0
            body = {
                "message": f"chore(version): {name or 'versionCode'} ({code}) [skip ci]",
                "content": base64.b64encode(rendered.encode()).decode(),
                "branch": branch,
            }
            if sha:
                body["sha"] = sha
            try:
                github("PUT", url, token, body)
            except urllib.error.HTTPError as exc:
                if exc.code in (409, 422) and attempt < 8:
                    time.sleep(attempt * 2)
                    continue
                raise
            print(f"Recorded {name or 'versionCode'} ({code}) in {repository}@{branch}:{version_file}")
            return 0
        return 1
    print(f"::error::Unknown mode {mode}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

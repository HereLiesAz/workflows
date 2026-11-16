#!/usr/bin/env python3
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def fail(message: str) -> None:
    print(f"::error::{message}", flush=True)
    raise SystemExit(1)


def run(*args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        list(args),
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return completed.stdout.strip() if capture else ""


def gh(*args: str, capture: bool = False) -> str:
    return run("gh", *args, capture=capture)


def git(*args: str, capture: bool = False) -> str:
    return run("git", *args, capture=capture)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def env_bool(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if value not in {"true", "false"}:
        fail(f"{name} must be true or false")
    return value == "true"


repo = os.environ.get("TARGET_REPOSITORY", "").strip()
target_sha = os.environ.get("TARGET_SHA", "").strip().lower()
build_version = os.environ.get("BUILD_VERSION", "").strip()
asset_glob = os.environ.get("ASSET_GLOB", "").strip()
title_prefix = os.environ.get("TITLE_PREFIX", "").strip()
asset_name_mode = os.environ.get("ASSET_NAME_MODE", "inject-version").strip()
notes_file = os.environ.get("NOTES_FILE", "").strip()
tag_prefix = os.environ.get("TAG_PREFIX", "")
prerelease = env_bool("PRERELEASE")
make_latest = env_bool("MAKE_LATEST")
migrate_legacy = env_bool("MIGRATE_LEGACY_BUILD_RELEASES")
# "patch" groups under MAJOR.MINOR.PATCH (patch-grouped-release); "minor" under MAJOR.MINOR.
group_level = os.environ.get("GROUP_LEVEL", "minor").strip()

if not os.environ.get("GH_TOKEN"):
    fail("github-token is required")
if not re.fullmatch(r"[^/]+/[^/]+", repo):
    fail("target-repository must be owner/name")
if not re.fullmatch(r"[0-9a-f]{40}", target_sha):
    fail("target-sha must be a full 40-character commit SHA")
match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", build_version)
if not match:
    fail("build-version must be MAJOR.MINOR.PATCH.BUILD")
if not asset_glob:
    fail("assets glob is required")
if not title_prefix:
    fail("title-prefix is required")
if group_level not in {"minor", "patch"}:
    fail("group-level must be minor or patch")
if asset_name_mode not in {"inject-version", "require-version"}:
    fail("asset-name-mode must be inject-version or require-version")

group_version = ".".join(match.groups()[: 3 if group_level == "patch" else 2])
build_tag = f"{tag_prefix}{build_version}"
group_tag = f"{tag_prefix}{group_version}"
group_title = f"{title_prefix} {group_version}"

raw_assets = [Path(item) for item in sorted(glob.glob(asset_glob, recursive=True)) if Path(item).is_file()]
if not raw_assets:
    fail(f"No release assets matched: {asset_glob}")


def name_with_version(name: str, version: str) -> str:
    if version in name:
        return name
    for suffix in (".tar.gz", ".tar.xz", ".tar.bz2"):
        if name.endswith(suffix):
            return f"{name[:-len(suffix)]}-{version}{suffix}"
    path = Path(name)
    if path.suffix:
        return f"{path.stem}-{version}{path.suffix}"
    return f"{name}-{version}"


asset_stage = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "minor-grouped-assets"
if asset_stage.exists():
    shutil.rmtree(asset_stage)
asset_stage.mkdir(parents=True, exist_ok=True)
assets: list[Path] = []
for asset in raw_assets:
    if build_version in asset.name:
        assets.append(asset)
        continue
    if asset_name_mode == "require-version":
        fail(
            f"Asset {asset.name!r} does not contain exact build version {build_version}; "
            "refusing a collision-prone grouped release"
        )
    staged = asset_stage / name_with_version(asset.name, build_version)
    shutil.copy2(asset, staged)
    assets.append(staged)

git("config", "user.name", "github-actions[bot]")
git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
git(
    "remote",
    "set-url",
    "origin",
    f"https://x-access-token:{os.environ['GH_TOKEN']}@github.com/{repo}.git",
)
git("fetch", "--force", "--tags", "origin")


def tag_target(tag: str) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        return None
    return git("rev-list", "-n", "1", tag, capture=True).lower()


def ensure_immutable_tag(tag: str, sha: str, message: str) -> None:
    existing = tag_target(tag)
    if existing is not None:
        if existing != sha:
            fail(f"Immutable tag {tag} already points to {existing}; refusing to move it to {sha}")
        return
    git("tag", "-a", tag, sha, "-m", message)
    ref = f"refs/tags/{tag}"
    push = subprocess.run(
        ["git", "push", "origin", ref],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if push.returncode == 0:
        return

    # GitHub can refuse a tag push from a GitHub App token that lacks `workflows`
    # permission when the tagged history touches `.github/workflows`, even though the
    # tag only names a commit that is already on the remote. The Git database API does
    # not apply that rule, so create the same annotated tag through REST. Never move an
    # existing immutable tag: an exact existing ref is retained only if it already
    # points at the same commit.
    print(f"Git push of {ref} was rejected: {push.stderr.strip()}", flush=True)

    def remote_commit() -> str | None:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/git/ref/tags/{tag}"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            return None
        response = json.loads(result.stdout)
        if not isinstance(response, dict) or response.get("ref") != ref:
            return None
        obj = response.get("object") or {}
        if obj.get("type") == "tag":
            peeled = subprocess.run(
                ["gh", "api", f"repos/{repo}/git/tags/{obj.get('sha')}"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if peeled.returncode != 0:
                return None
            return str((json.loads(peeled.stdout).get("object") or {}).get("sha") or "").lower() or None
        return str(obj.get("sha") or "").lower() or None

    def retain_if_same(reason: str) -> bool:
        existing_remote = remote_commit()
        if existing_remote is None:
            return False
        if existing_remote != sha:
            fail(f"Immutable tag {tag} already points to {existing_remote}; refusing to move it to {sha}")
        print(f"Immutable tag {tag} {reason}; retaining it.", flush=True)
        return True

    if retain_if_same("already exists"):
        return

    try:
        tag_object = json.loads(
            gh(
                "api", "--method", "POST", f"repos/{repo}/git/tags",
                "-f", f"tag={tag}",
                "-f", f"message={message}",
                "-f", f"object={sha}",
                "-f", "type=commit",
                capture=True,
            )
        )
        tag_sha = tag_object.get("sha")
        if not isinstance(tag_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", tag_sha):
            fail(f"GitHub returned no valid annotated tag object for {tag}")
        gh(
            "api", "--method", "POST", f"repos/{repo}/git/refs",
            "-f", f"ref={ref}", "-f", f"sha={tag_sha}",
        )
    except subprocess.CalledProcessError:
        if retain_if_same("appeared concurrently"):
            return
        # Last resort: GitHub creates the tag itself when a release names a tag that does
        # not exist yet. The holder release is folded into the grouped release below by
        # the legacy migration, which keeps the exact tag.
        print(f"Git push and ref creation for {ref} were refused; creating it through a release.", flush=True)
        try:
            gh(
                "release", "create", tag,
                "--repo", repo,
                "--target", sha,
                "--prerelease",
                "--title", message,
                "--notes", "Build tag created by the release publisher; folded into the grouped release.",
            )
        except subprocess.CalledProcessError:
            if retain_if_same("appeared concurrently"):
                return
            fail(f"Could not create immutable tag {tag} via Git push, GitHub API or a release")
        if not retain_if_same("created through a release"):
            fail(f"Release creation for {tag} reported success but the tag is missing")


def ensure_group_tag() -> None:
    if tag_target(group_tag) is not None:
        return
    git("tag", "-a", group_tag, target_sha, "-m", f"{group_title} grouped release")
    ref = f"refs/tags/{group_tag}"
    push = subprocess.run(
        ["git", "push", "origin", ref],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if push.returncode == 0:
        return

    # GitHub can reject an otherwise valid grouped tag push with only "(failed)".
    # Do not force-push or move a grouped tag: first check whether a concurrent
    # publisher created it, then try the Git database API with the same token.
    print(f"Git push of {ref} was rejected: {push.stderr.strip()}", flush=True)

    def exists_remotely() -> bool:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/git/ref/tags/{group_tag}"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            return False
        response = json.loads(result.stdout)
        # GitHub's single-ref GET also returns prefix matches. An exact match
        # is required, or 0.12.35.1 would impersonate missing 0.12.35.
        return isinstance(response, dict) and response.get("ref") == ref

    if exists_remotely():
        print(f"Grouped tag {group_tag} already exists; retaining it.", flush=True)
        return

    try:
        # Preserve the existing annotated-tag contract, even when using REST
        # to create the ref rather than Git transport.
        tag_object = json.loads(
            gh(
                "api", "--method", "POST", f"repos/{repo}/git/tags",
                "-f", f"tag={group_tag}",
                "-f", f"message={group_title} grouped release",
                "-f", f"object={target_sha}",
                "-f", "type=commit",
                capture=True,
            )
        )
        tag_sha = tag_object.get("sha")
        if not isinstance(tag_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", tag_sha):
            fail(f"GitHub returned no valid annotated tag object for {group_tag}")
        gh(
            "api", "--method", "POST", f"repos/{repo}/git/refs",
            "-f", f"ref={ref}", "-f", f"sha={tag_sha}",
        )
    except subprocess.CalledProcessError:
        if exists_remotely():
            print(f"Grouped tag {group_tag} appeared concurrently; retaining it.", flush=True)
            return
        fail(f"Could not create grouped tag {group_tag} via Git push or GitHub API")


def release_json(tag: str) -> dict | None:
    completed = subprocess.run(
        ["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        return None
    return json.loads(completed.stdout)


def write_notes(path: Path) -> None:
    tags = git("tag", "-l", f"{tag_prefix}{group_version}.*", "--sort=-v:refname", capture=True)
    exact_pattern = re.compile(
        "^" + re.escape(tag_prefix + group_version) + (r"\.\d+$" if group_level == "patch" else r"\.\d+\.\d+$")
    )
    exact_tags = [tag for tag in tags.splitlines() if exact_pattern.fullmatch(tag)]

    lines = [
        f"# {group_title}",
        "",
        f"All immutable **{group_version}.x** builds"
        + ("" if group_level == "patch" else ", across every patch,")
        + " are grouped in this release.",
        "",
        f"Latest published build in this run: **{build_version}** from commit {target_sha}.",
        "",
        "## Immutable build tags",
    ]
    lines.extend(f"- {tag}" for tag in exact_tags)
    note_path = Path(notes_file) if notes_file else None
    if note_path and note_path.is_file() and note_path.stat().st_size:
        lines.extend(["", f"## Changes in {build_version}", note_path.read_text(encoding="utf-8")])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def edit_release(notes_path: Path) -> None:
    args = [
        "release",
        "edit",
        group_tag,
        "--repo",
        repo,
        "--title",
        group_title,
        "--notes-file",
        str(notes_path),
    ]
    if prerelease:
        args.append("--prerelease")
    if make_latest:
        args.append("--latest")
    gh(*args)


def ensure_group_release(notes_path: Path) -> None:
    if release_json(group_tag) is not None:
        edit_release(notes_path)
        return
    args = [
        "release",
        "create",
        group_tag,
        "--repo",
        repo,
        "--verify-tag",
        "--title",
        group_title,
        "--notes-file",
        str(notes_path),
    ]
    if prerelease:
        args.append("--prerelease")
    if make_latest:
        args.append("--latest")
    gh(*args)


def existing_asset(tag: str, name: str) -> dict | None:
    release = release_json(tag)
    if release is None:
        return None
    return next((asset for asset in release.get("assets", []) if asset.get("name") == name), None)


def upload_idempotently(tag: str, file: Path) -> None:
    local_digest = sha256(file)
    remote = existing_asset(tag, file.name)
    if remote is not None:
        digest = str(remote.get("digest") or "")
        if digest == f"sha256:{local_digest}":
            print(f"Asset {file.name} already exists with identical SHA-256; keeping it.")
            return
        with tempfile.TemporaryDirectory(prefix="minor-release-compare-") as directory:
            gh(
                "release",
                "download",
                tag,
                "--repo",
                repo,
                "--pattern",
                file.name,
                "--dir",
                directory,
            )
            downloaded = Path(directory) / file.name
            if not downloaded.is_file() or sha256(downloaded) != local_digest:
                fail(f"Grouped release already contains different bytes for {file.name}")
        print(f"Asset {file.name} already exists with identical bytes; keeping it.")
        return
    gh("release", "upload", tag, str(file), "--repo", repo)


def legacy_release_tags() -> list[str]:
    pages = json.loads(
        gh(
            "api",
            "--paginate",
            "--slurp",
            f"repos/{repo}/releases?per_page=100",
            capture=True,
        )
    )
    payload = [item for page in pages for item in page]
    # Minor level matches both old one-release-per-build tags (MAJOR.MINOR.PATCH.BUILD) and old
    # one-release-per-patch tags (MAJOR.MINOR.PATCH). Patch level matches per-build tags only.
    suffix = r"\.\d+$" if group_level == "patch" else r"\.\d+(?:\.\d+)?$"
    pattern = re.compile("^" + re.escape(tag_prefix + group_version) + suffix)
    return sorted(
        {
            str(item.get("tag_name"))
            for item in payload
            if pattern.fullmatch(str(item.get("tag_name") or ""))
            and str(item.get("tag_name")) != group_tag
        }
    )


def migrate_release(tag: str) -> None:
    release = release_json(tag)
    if release is None:
        return
    with tempfile.TemporaryDirectory(prefix="legacy-build-release-") as directory:
        if release.get("assets"):
            gh("release", "download", tag, "--repo", repo, "--dir", directory)
            legacy_version = tag[len(tag_prefix):] if tag.startswith(tag_prefix) else tag
            for file in sorted(Path(directory).iterdir()):
                if not file.is_file():
                    continue
                if legacy_version not in file.name:
                    renamed = Path(directory) / name_with_version(file.name, legacy_version)
                    file.rename(renamed)
                    file = renamed
                upload_idempotently(group_tag, file)
    # Deliberately omit --cleanup-tag. Exact build tags remain immutable and discoverable.
    gh("release", "delete", tag, "--repo", repo, "--yes")


ensure_immutable_tag(build_tag, target_sha, f"{title_prefix} {build_version}")
ensure_group_tag()

with tempfile.TemporaryDirectory(prefix="minor-release-notes-") as directory:
    release_notes = Path(directory) / "notes.md"
    write_notes(release_notes)
    ensure_group_release(release_notes)

    if migrate_legacy:
        for legacy_tag in legacy_release_tags():
            print(f"Migrating legacy release {legacy_tag} into {group_tag}; preserving its tag.")
            migrate_release(legacy_tag)

    for asset in assets:
        upload_idempotently(group_tag, asset)

    write_notes(release_notes)
    edit_release(release_notes)

print(f"Grouped {build_tag} under GitHub Release {group_tag}.")

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CANONICAL_KEYS = ("versionMajor", "versionMinor", "versionPatch", "versionBuild")
ALIASES = {
    "versionMajor": ("versionMajor", "MAJOR", "VERSION_MAJOR"),
    "versionMinor": ("versionMinor", "MINOR", "VERSION_MINOR"),
    "versionPatch": ("versionPatch", "PATCH", "VERSION_PATCH"),
    "versionBuild": ("versionBuild", "BUILD", "BUILD_NUMBER", "VERSION_BUILD"),
}
VERSION_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?(?!\d)")
FEATURE_RE = re.compile(
    r"(?im)(?:^|\n)\s*(?:feat|feature)(?:\([^\n)]*\))?!?:|\[(?:minor|feature)\]|version\s*:\s*minor"
)


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int
    build: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}.{self.build}"

    @property
    def android_version_code(self) -> int:
        if not (0 <= self.major <= 20):
            raise ValueError("major must be between 0 and 20 for Android versionCode encoding")
        if not (0 <= self.minor <= 99):
            raise ValueError("minor must be between 0 and 99 for Android versionCode encoding")
        if not (0 <= self.patch <= 99):
            raise ValueError("patch must be between 0 and 99 for Android versionCode encoding")
        if not (0 <= self.build <= 9999):
            raise ValueError("build must be between 0 and 9999 for Android versionCode encoding")
        value = self.major * 100_000_000 + self.minor * 1_000_000 + self.patch * 10_000 + self.build
        if value > 2_100_000_000:
            raise ValueError("encoded Android versionCode exceeds Google Play's limit")
        return value


def run(*args: str, check: bool = True, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout}{proc.stderr}"
        )
    return proc.stdout.strip()


def parse_property_lines(text: str) -> tuple[list[str], dict[str, str]]:
    lines = text.splitlines()
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return lines, values


def _first_int(values: dict[str, str], names: Iterable[str]) -> int | None:
    for name in names:
        raw = values.get(name)
        if raw is None:
            continue
        if re.fullmatch(r"\d+", raw):
            return int(raw)
    return None


def version_from_properties(text: str) -> Version | None:
    _, values = parse_property_lines(text)
    parts: list[int] = []
    for key in CANONICAL_KEYS:
        value = _first_int(values, ALIASES[key])
        if value is None:
            return None
        parts.append(value)
    return Version(*parts)


def version_from_text(text: str) -> Version | None:
    found: list[Version] = []
    for match in VERSION_RE.finditer(text):
        found.append(
            Version(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4) or 0),
            )
        )
    return max(found) if found else None


def render_properties(existing: str, version: Version) -> str:
    lines, _ = parse_property_lines(existing)
    canonical = {
        "versionMajor": str(version.major),
        "versionMinor": str(version.minor),
        "versionPatch": str(version.patch),
        "versionBuild": str(version.build),
    }
    alias_values: dict[str, str] = {}
    for canonical_key, aliases in ALIASES.items():
        for alias in aliases:
            alias_values[alias] = canonical[canonical_key]

    seen_canonical: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            out.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in alias_values:
            canonical_key = next(k for k, aliases in ALIASES.items() if key in aliases)
            if key == canonical_key:
                seen_canonical.add(canonical_key)
            out.append(f"{key}={alias_values[key]}")
        else:
            out.append(line)

    missing = [key for key in CANONICAL_KEYS if key not in seen_canonical]
    if missing:
        prefix = [f"{key}={canonical[key]}" for key in missing]
        if out and out[0].strip():
            prefix.append("")
        out = prefix + out
    return "\n".join(out).rstrip() + "\n"


def state_payload(source_sha: str, version: Version, run_id: str) -> str:
    return json.dumps(
        {
            "schema": 1,
            "source_sha": source_sha,
            "version": str(version),
            "run_id": run_id,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def parse_state(text: str) -> tuple[str, Version | None]:
    try:
        data = json.loads(text)
    except Exception:
        return "", None
    if not isinstance(data, dict):
        return "", None
    source_sha = str(data.get("source_sha") or "")
    version = version_from_text(str(data.get("version") or ""))
    return source_sha, version


def git_show(ref: str, path: str) -> str:
    return run("git", "show", f"{ref}:{path}", check=False)


def commit_message(sha: str) -> str:
    return run("git", "show", "-s", "--format=%B", sha)


def classify_next(
    previous: Version,
    previous_source_sha: str,
    target_sha: str,
    source_version: Version | None,
    message: str,
) -> tuple[Version, str]:
    if previous_source_sha == target_sha:
        return Version(previous.major, previous.minor, previous.patch, previous.build + 1), "build"

    if source_version is not None and source_version.major > previous.major:
        return Version(source_version.major, 0, 0, 1), "major"
    if source_version is not None and source_version.major < previous.major:
        source_version = None

    if (
        source_version is not None
        and source_version.major == previous.major
        and source_version.minor > previous.minor
    ):
        return Version(previous.major, source_version.minor, 0, 1), "minor"

    if (
        source_version is not None
        and source_version.major == previous.major
        and source_version.minor == previous.minor
        and source_version.patch > previous.patch
    ):
        return Version(previous.major, previous.minor, source_version.patch, 1), "patch"

    if FEATURE_RE.search(message):
        return Version(previous.major, previous.minor + 1, 0, 1), "minor"

    return Version(previous.major, previous.minor, previous.patch + 1, 1), "patch"


def write_github_file(path: str | None, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def resolve_state_branch(repository: str, ref_name: str, ref_type: str) -> str:
    if ref_type == "branch" and ref_name:
        return ref_name
    return run("gh", "api", f"repos/{repository}", "--jq", ".default_branch")


def apply_contract(
    repository: str,
    target_sha: str,
    ref_name: str,
    ref_type: str,
    workspace: Path,
    run_id: str,
    max_attempts: int = 8,
) -> tuple[Version, str]:
    os.chdir(workspace)
    state_branch = resolve_state_branch(repository, ref_name, ref_type)
    run("gh", "auth", "setup-git")

    for attempt in range(1, max_attempts + 1):
        run("git", "fetch", "--force", "origin", f"refs/heads/{state_branch}:refs/remotes/origin/{state_branch}")
        branch_ref = f"origin/{state_branch}"

        persisted_props = git_show(branch_ref, "version.properties")
        persisted_state = git_show(branch_ref, ".version-state.json")
        previous = version_from_properties(persisted_props)
        state_source, state_version = parse_state(persisted_state)

        source_props = git_show(target_sha, "version.properties")
        source_version = version_from_properties(source_props)

        if previous is None:
            previous = source_version or version_from_text(
                run("git", "tag", "--sort=-version:refname", check=False)
            ) or Version(0, 0, 0, 0)

        if state_version is not None:
            previous = state_version
        if not state_source:
            state_source = target_sha

        version, bump = classify_next(
            previous,
            state_source,
            target_sha,
            source_version,
            commit_message(target_sha),
        )

        # Fail early if this build may need an Android versionCode.
        try:
            android_code = version.android_version_code
        except ValueError:
            android_code = -1

        run("git", "switch", "--detach", branch_ref)
        Path("version.properties").write_text(
            render_properties(persisted_props or source_props, version),
            encoding="utf-8",
        )
        Path(".version-state.json").write_text(
            state_payload(target_sha, version, run_id),
            encoding="utf-8",
        )
        run("git", "config", "user.name", "github-actions[bot]")
        run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        run("git", "add", "version.properties", ".version-state.json")

        if run("git", "diff", "--cached", "--quiet", check=False) == "":
            # diff --quiet writes no output on both success/failure; inspect return code instead.
            pass
        proc = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if proc.returncode != 0:
            run(
                "git",
                "commit",
                "-m",
                f"chore(version): {version} ({bump}) [skip ci]",
            )
            push = subprocess.run(
                ["git", "push", "origin", f"HEAD:refs/heads/{state_branch}"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if push.returncode != 0:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"could not persist version after {max_attempts} attempts:\n"
                        f"{push.stdout}{push.stderr}"
                    )
                time.sleep(min(attempt * 2, 10))
                continue

        outputs = {
            "version": str(version),
            "major": str(version.major),
            "minor": str(version.minor),
            "patch": str(version.patch),
            "build": str(version.build),
            "bump": bump,
            "state_branch": state_branch,
            "android_version_code": str(android_code),
        }
        write_github_file(os.environ.get("GITHUB_OUTPUT"), outputs)
        write_github_file(
            os.environ.get("GITHUB_ENV"),
            {
                "VERSION": str(version),
                "VERSION_MAJOR": str(version.major),
                "VERSION_MINOR": str(version.minor),
                "VERSION_PATCH": str(version.patch),
                "VERSION_BUILD": str(version.build),
                "ANDROID_VERSION_CODE": str(android_code),
            },
        )
        return version, bump

    raise RuntimeError("version contract retry loop exhausted")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the HereLiesAz major.minor.patch.build contract.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--ref-name", default="")
    parser.add_argument("--ref-type", default="")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    args = parser.parse_args()

    version, bump = apply_contract(
        repository=args.repository,
        target_sha=args.target_sha,
        ref_name=args.ref_name,
        ref_type=args.ref_type,
        workspace=Path(args.workspace).resolve(),
        run_id=args.run_id,
    )
    print(f"{version} ({bump})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

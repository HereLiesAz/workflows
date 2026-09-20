#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path


def fail(message: str) -> None:
    print(f"::error::{message}", flush=True)
    raise SystemExit(1)


source = os.environ.get("SOURCE_VERSION", "").strip()
source_file = os.environ.get("SOURCE_VERSION_FILE", "").strip()
source_key = os.environ.get("SOURCE_VERSION_KEY", "").strip()
build_number = os.environ.get("BUILD_NUMBER", "").strip()
prerelease_major_max = os.environ.get("PRERELEASE_MAJOR_MAX", "0").strip()
environment_variable = os.environ.get("ENVIRONMENT_VARIABLE", "").strip()

if not source:
    if not source_file or not source_key:
        fail("Provide source-version or both source-version-file and source-version-key")
    path = Path(source_file)
    if not path.is_file():
        fail(f"Version source file does not exist: {source_file}")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == source_key:
            source = value.strip()
            break
    if not source:
        fail(f"Version key {source_key!r} not found in {source_file}")

match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", source)
if not match:
    fail("Source version must be MAJOR.MINOR.PATCH.BUILD")

if not re.fullmatch(r"\d+", build_number):
    fail("build-number must be a non-negative integer")
if not re.fullmatch(r"\d+", prerelease_major_max):
    fail("prerelease-major-max must be a non-negative integer")
if environment_variable and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", environment_variable):
    fail("environment-variable must be a valid environment variable name")

major, minor, patch, _ = (int(item) for item in match.groups())
version = f"{major}.{minor}.{patch}.{int(build_number)}"
patch_version = f"{major}.{minor}.{patch}"
prerelease = major <= int(prerelease_major_max)

output = Path(os.environ["GITHUB_OUTPUT"])
with output.open("a", encoding="utf-8") as handle:
    handle.write(f"version={version}\n")
    handle.write(f"patch-version={patch_version}\n")
    handle.write(f"prerelease={'true' if prerelease else 'false'}\n")

if environment_variable:
    env_file = Path(os.environ["GITHUB_ENV"])
    with env_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{environment_variable}={version}\n")

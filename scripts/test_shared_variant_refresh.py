#!/usr/bin/env python3
from __future__ import annotations

from shared_workflow_library import add_shared_variant, build_shared_family, family_variants


def compiled(command: str) -> str:
    return f'''name: release\non:\n  workflow_dispatch:\n    inputs:\n      target_repository:\n        required: true\n        type: string\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - run: {command}\n'''


variant = "0123456789abcdef"
old_family = build_shared_family("node-release", [(variant, compiled("echo-old"))])
assert "echo-old" in old_family
assert family_variants(old_family) == {variant}

refreshed = add_shared_variant(
    old_family,
    "node-release",
    variant,
    compiled("echo-new"),
)
assert "echo-new" in refreshed
assert "echo-old" not in refreshed
assert family_variants(refreshed) == {variant}
assert refreshed.count(f"v_{variant}__release:") == 1
print("shared variant refresh regression test passed")

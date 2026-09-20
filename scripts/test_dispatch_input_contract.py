#!/usr/bin/env python3
from __future__ import annotations

import dispatch_request
from dispatch_request import (
    conform_dispatch_inputs,
    declared_dispatch_inputs,
    validate_central_workflow_binding,
)


def main() -> int:
    play = ".github/workflows/android-play-release.yml"
    declared = declared_dispatch_inputs(play)

    assert len(declared) == 25, f"expected Play workflow at GitHub's 25-input ceiling, got {len(declared)}"
    assert "purpose_profile_json" in declared
    assert "target_workflow_ref" not in declared

    candidate = {name: "fixture" for name in declared}
    # This was the production failure: generic metadata supplied a 26th property that the generalized
    # Play workflow did not declare. The dispatcher must drop it before calling GitHub.
    candidate["target_workflow_ref"] = "HereLiesAz/Guillotine/.github/workflows/release-aab.yml@refs/heads/main"

    filtered = conform_dispatch_inputs(play, candidate)
    assert len(filtered) == 25
    assert set(filtered) == set(declared)
    assert "target_workflow_ref" not in filtered

    original_policy = dispatch_request.validation_errors_for_workflow
    try:
        dispatch_request.validation_errors_for_workflow = lambda _: [
            "repository-generated executor must not be generalized-policy validated"
        ]
        validate_central_workflow_binding(
            "HereLiesAz/aive",
            "repository",
            ".github/workflows/aive-live-runtime-verification.yml",
        )

        try:
            validate_central_workflow_binding(
                "HereLiesAz/aive",
                "repository",
                ".github/workflows/other-live-runtime-verification.yml",
            )
        except RuntimeError as exc:
            assert "outside its namespace" in str(exc)
        else:
            raise AssertionError("repository binding accepted an executor outside its namespace")

        try:
            validate_central_workflow_binding(
                "HereLiesAz/aive",
                "curated",
                ".github/workflows/generalized-live-runtime-verification.yml",
            )
        except RuntimeError as exc:
            assert "generalized workflow policy" in str(exc)
        else:
            raise AssertionError("curated binding bypassed generalized policy")
    finally:
        dispatch_request.validation_errors_for_workflow = original_policy

    print("dispatch input contract regression: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

from dispatch_request import conform_dispatch_inputs, declared_dispatch_inputs


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

    print("dispatch input contract regression: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

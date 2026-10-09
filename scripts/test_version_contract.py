#!/usr/bin/env python3
from __future__ import annotations

from version_contract import (
    Version,
    classify_next,
    recorded_for_trigger,
    state_payload,
    version_from_properties,
)


def expect(actual, expected):
    assert actual == expected, f"expected {expected!r}, got {actual!r}"


def main() -> int:
    expect(
        version_from_properties(
            "versionMajor=1\nversionMinor=2\nversionPatch=3\nversionBuild=4\n"
        ),
        Version(1, 2, 3, 4),
    )
    expect(
        version_from_properties("major=7\nminor=8\npatch=9\n"),
        Version(7, 8, 9, 0),
    )
    expect(
        version_from_properties("versionMajor=5\n"),
        Version(5, 0, 0, 0),
    )

    # One push dispatches Play and GitHub runs of one commit: the second reuses the first's version.
    recorded = state_payload("abc", Version(1, 2, 3, 4), "run-1", "delivery-1")
    expect(recorded_for_trigger(recorded, "abc", "delivery-1"), Version(1, 2, 3, 4))
    # A new event on the same commit (a rebuild) advances instead.
    expect(recorded_for_trigger(recorded, "abc", "delivery-2"), None)
    # A different commit, or no trigger id, never reuses.
    expect(recorded_for_trigger(recorded, "def", "delivery-1"), None)
    expect(recorded_for_trigger(recorded, "abc", ""), None)
    # State written before trigger ids existed never matches.
    expect(recorded_for_trigger(state_payload("abc", Version(1, 2, 3, 4), "run-1"), "abc", "delivery-1"), None)
    expect(recorded_for_trigger("not json", "abc", "delivery-1"), None)

    previous = Version(3, 4, 5, 9)

    version, bump = classify_next(
        previous,
        "same",
        "same",
        Version(3, 4, 5, 9),
        "recompile",
    )
    expect((version, bump), (Version(3, 4, 5, 10), "build"))

    version, bump = classify_next(
        previous,
        "old",
        "new",
        Version(4, 99, 99, 99),
        "Owner changes major",
    )
    expect((version, bump), (Version(4, 0, 0, 1), "major"))

    version, bump = classify_next(
        previous,
        "old",
        "new",
        Version(3, 5, 99, 99),
        "AI feature version edit",
    )
    expect((version, bump), (Version(3, 5, 0, 1), "minor"))

    version, bump = classify_next(
        previous,
        "old",
        "new",
        Version(3, 4, 5, 9),
        "feat: add new functionality",
    )
    expect((version, bump), (Version(3, 5, 0, 1), "minor"))

    version, bump = classify_next(
        previous,
        "old",
        "new",
        Version(3, 4, 5, 9),
        "Refactor existing behavior\n\nVersion-Impact: minor",
    )
    expect((version, bump), (Version(3, 5, 0, 1), "minor"))

    version, bump = classify_next(
        previous,
        "old",
        "new",
        Version(3, 4, 99, 99),
        "fix: change existing behavior",
    )
    expect((version, bump), (Version(3, 4, 6, 1), "patch"))

    version, bump = classify_next(
        previous,
        "old",
        "new",
        Version(3, 4, 5, 9),
        "docs: ordinary non-feature source change",
    )
    expect((version, bump), (Version(3, 4, 6, 1), "patch"))

    print("version contract regression test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

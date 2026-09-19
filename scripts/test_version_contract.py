#!/usr/bin/env python3
from __future__ import annotations

from version_contract import (
    Version,
    classify_next,
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

#!/usr/bin/env python3
"""Regression tests for the single Android versioning rule (.github/actions/android-version)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "android_version", Path(__file__).resolve().parents[1] / ".github/actions/android-version/version.py"
)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

props = v.parse_properties("versionMajor=0\nversionMinor=11\nversionPatch=7\nversionBuild=1\n")
assert v.next_pair(props, 0) == (1, "0.11.7.2"), "first release: code 1, last field +1"
assert v.next_pair(props, 110070001) == (110070002, "0.11.7.2"), "Play's highest wins, plus exactly one"

recorded = v.parse_properties("versionMajor=1\nversionMinor=2\nversionPatch=3\nversionCode=57\nversionName=1.2.3.9\n")
assert v.next_pair(recorded, 40) == (58, "1.2.3.10"), "recorded code wins over a lower Play code"
assert v.next_pair(recorded, 57) == (58, "1.2.3.10"), "equal codes still advance by one"

bumped = v.parse_properties("versionMajor=1\nversionMinor=3\nversionPatch=0\nversionCode=57\nversionName=1.2.3.9\n")
assert v.next_pair(bumped, 0) == (58, "1.3.0.10"), "hand-edited major.minor.patch is taken; last field still +1"

text = "# header\nversionMajor=1\nversionBuild=9\nversionName=old\nother=x\n"
out = v.render_recorded(text, 58, "1.2.3.10")
assert out == "# header\nversionMajor=1\nversionBuild=10\nversionName=1.2.3.10\nother=x\nversionCode=58\n", out
assert v.render_recorded("", 1, "0.0.0.1") == "versionCode=1\nversionName=0.0.0.1\nversionBuild=1\n"
print("android version tests passed")

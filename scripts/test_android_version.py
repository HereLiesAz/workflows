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
assert v.render_recorded("versionCode=90\nversionName=1.2.3.9\n", 58, "") == "versionCode=90\nversionName=1.2.3.9\n", \
    "a recorded versionCode is never lowered"
assert v.render_recorded("versionCode=57\nversionName=1.2.3.9\nversionBuild=9\n", 58) == \
    "versionCode=58\nversionName=1.2.3.9\nversionBuild=9\n", "code-only record leaves the name alone"

# Both Android release workflows take versionCode from this rule and nothing else: no version-name
# encoding, no fallback when Play can't be read.
root = Path(__file__).resolve().parents[1]
for name in ("android-play-release.yml", "android-github-release.yml"):
    text = (root / ".github/workflows" / name).read_text(encoding="utf-8")
    assert "HereLiesAz/workflows/.github/actions/android-version@" in text, f"{name} must use the android-version action"
    assert "outputs.android_version_code" not in text, f"{name} must not use the version-name encoding"
    assert "falling back" not in text, f"{name} must fail rather than fall back"
# A Play edit replaced by another run mid-read is re-read, not fatal.
import sys
import types


class FakeHttpError(Exception):
    def __init__(self, status, content):
        super().__init__(content)
        self.resp = types.SimpleNamespace(status=status)
        self.content = content


class Call:
    def __init__(self, fn):
        self.fn = fn

    def execute(self, num_retries=0):
        return self.fn()


class FakeEdits:
    def __init__(self):
        self.inserts = 0

    def insert(self, packageName, body):
        self.inserts += 1
        return Call(lambda: {"id": f"e{self.inserts}"})

    def delete(self, packageName, editId):
        def run():
            if editId == "e1":
                raise FakeHttpError(400, b"This Edit has been deleted.")
        return Call(run)

    def bundles(self):
        return types.SimpleNamespace(list=lambda packageName, editId: Call(lambda: {"bundles": [{"versionCode": "41"}]}))

    def apks(self):
        def listing(packageName, editId):
            def run():
                if editId == "e1":
                    raise FakeHttpError(400, b"This Edit has been deleted.")
                return {"apks": [{"versionCode": "42"}]}
            return Call(run)
        return types.SimpleNamespace(list=listing)

    def tracks(self):
        return types.SimpleNamespace(list=lambda packageName, editId: Call(lambda: {"tracks": []}))


fake = FakeEdits()
for name, attrs in {
    "google": {},
    "google.oauth2": {},
    "google.oauth2.service_account": {"Credentials": types.SimpleNamespace(from_service_account_info=lambda info, scopes: None)},
    "googleapiclient": {},
    "googleapiclient.discovery": {"build": lambda *a, **k: types.SimpleNamespace(edits=lambda: fake)},
    "googleapiclient.errors": {"HttpError": FakeHttpError},
}.items():
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module
sys.modules["google.oauth2"].service_account = sys.modules["google.oauth2.service_account"]
v.time.sleep = lambda seconds: None
assert v.play_highest_code("{}", "com.example") == 42, "a replaced edit is re-read on a fresh edit"
assert fake.inserts == 2

print("android version tests passed")

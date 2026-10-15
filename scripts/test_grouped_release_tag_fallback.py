#!/usr/bin/env python3
"""Exercise the real grouped-tag publisher with mocked Git and GitHub calls."""
from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / ".github/actions/minor-grouped-release/publish.py"
source_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
declaration = next(node for node in source_tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == "ensure_group_tag")
source_code = compile(ast.Module(body=[declaration], type_ignores=[]), str(SOURCE), "exec")
TAG_SHA = "a" * 40
COMMIT_SHA = "b" * 40


def scenario(*, push_success=False, remote_exists=False, api_ref_conflict=False,
             api_tag_failure=False, prefix_only=False):
    calls = []
    remote = [remote_exists]

    def fake_git(*args):
        calls.append(("git", *args))
        assert args == (
            "tag", "-a", "0.12.35", COMMIT_SHA, "-m", "illumera 0.12.35 grouped release"
        )

    def fake_gh(*args, capture=False):
        calls.append(("gh", *args))
        if "git/tags" in args[3]:
            if api_tag_failure:
                raise subprocess.CalledProcessError(422, args)
            return json.dumps({"sha": TAG_SHA})
        assert args[3] == "repos/HereLiesAz/illumera/git/refs"
        assert args[-2:] == ("-f", "sha=" + TAG_SHA)
        if api_ref_conflict:
            remote[0] = True
            raise subprocess.CalledProcessError(422, args)
        remote[0] = True
        return ""

    class FakeProcess:
        PIPE = subprocess.PIPE
        CalledProcessError = subprocess.CalledProcessError

        @staticmethod
        def run(args, **kwargs):
            calls.append(("run", *args))
            if args[0] == "git":
                assert args == ["git", "push", "origin", "refs/tags/0.12.35"]
                return subprocess.CompletedProcess(args, 0 if push_success else 1,
                                                   "", "" if push_success else "(failed)")
            assert args == [
                "gh", "api", "repos/HereLiesAz/illumera/git/ref/tags/0.12.35"
            ]
            if prefix_only:
                return subprocess.CompletedProcess(args, 0,
                                                   '[{"ref":"refs/tags/0.12.35.1"}]', "")
            if remote[0]:
                return subprocess.CompletedProcess(args, 0,
                                                   '{"ref":"refs/tags/0.12.35"}', "")
            return subprocess.CompletedProcess(args, 1, "", "HTTP 404")

    def fake_fail(message):
        calls.append(("fail", message))
        raise SystemExit(message)

    globals_ = {
        "group_tag": "0.12.35",
        "group_title": "illumera 0.12.35",
        "target_sha": COMMIT_SHA,
        "repo": "HereLiesAz/illumera",
        "tag_target": lambda tag: None,
        "git": fake_git,
        "gh": fake_gh,
        "subprocess": FakeProcess,
        "json": json,
        "re": re,
        "fail": fake_fail,
    }
    exec(source_code, globals_)
    try:
        globals_["ensure_group_tag"]()
        return calls, None
    except SystemExit as exc:
        return calls, str(exc)


calls, failure = scenario(push_success=True)
assert failure is None
assert not any(call[0] == "gh" for call in calls)

calls, failure = scenario()
assert failure is None
assert ("gh", "api", "--method", "POST", "repos/HereLiesAz/illumera/git/tags",
        "-f", "tag=0.12.35", "-f", "message=illumera 0.12.35 grouped release",
        "-f", "object=" + COMMIT_SHA, "-f", "type=commit") in calls
assert ("gh", "api", "--method", "POST", "repos/HereLiesAz/illumera/git/refs",
        "-f", "ref=refs/tags/0.12.35", "-f", "sha=" + TAG_SHA) in calls

calls, failure = scenario(remote_exists=True)
assert failure is None
assert not any(call[0] == "gh" for call in calls)

calls, failure = scenario(prefix_only=True)
assert failure is None
assert any(call[0] == "gh" for call in calls)  # Prefix-only ref cannot pass as exact.

calls, failure = scenario(api_ref_conflict=True)
assert failure is None  # Concurrent publisher created exact tag during REST creation.

calls, failure = scenario(api_tag_failure=True)
assert "Could not create grouped tag 0.12.35" in failure
assert not any(call[:4] == ("gh", "api", "--method", "POST") and
               "git/refs" in call[4] for call in calls)

print("Grouped release ref fallback: six independent scenarios passed.")

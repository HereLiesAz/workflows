#!/usr/bin/env python3
"""Regression tests for the Play publisher's resilience (run from the repository root).

Covers three behaviours of .github/workflows/android-play-release.yml:
  * a 403 "Daily save quota exceeded." on edits.commit defers the publish (exit 0, outputs, no
    record of a versionCode) instead of failing the run, while any other 403 still fails it;
  * the supersede check publishes only the newest commit, ignoring version-bookkeeping commits;
  * every central action reference is pinned to a commit whose action tree is the current one.
"""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAY = ROOT / ".github/workflows/android-play-release.yml"
text = PLAY.read_text(encoding="utf-8")


def heredoc_python() -> str:
    start = text.index("timeout 1800 python - <<'PY'\n") + len("timeout 1800 python - <<'PY'\n")
    end = text.index("\n          PY\n", start)
    return textwrap.dedent(text[start:end])


def supersede_shell() -> str:
    """The shared shell body of the supersede check, taken from the dedicated job."""
    start = text.index("  supersede_check:\n")
    run_at = text.index("        run: |\n", start) + len("        run: |\n")
    end = text.index('\n          echo "superseded=$superseded"', run_at)
    return textwrap.dedent(text[run_at:end])


FAKES = r'''
import json, os, sys, types

class Resp(dict):
    def __init__(self, status, headers=None):
        super().__init__(headers or {})
        self.status = status

class HttpError(Exception):
    def __init__(self, resp, content, uri=None):
        super().__init__(f"<HttpError {resp.status} returned {content!r}>")
        self.resp = resp
        self.content = content

def module(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod

COMMIT_ERROR = json.loads(os.environ["FAKE_COMMIT_ERROR"])
calls = []

class Request:
    def __init__(self, name, result=None, error=None):
        self.name, self.result, self.error = name, result, error
    def execute(self, num_retries=0):
        calls.append(self.name)
        if self.error:
            raise HttpError(Resp(self.error["status"], self.error.get("headers")), json.dumps({"error": {"message": self.error["message"]}}).encode())
        return self.result if self.result is not None else {}

class Chain:
    def __init__(self, prefix=""):
        self.prefix = prefix
    def __getattr__(self, name):
        path = f"{self.prefix}.{name}" if self.prefix else name
        def call(*args, **kwargs):
            if path == "edits.insert":
                return Request(path, {"id": "edit-1"})
            if path == "edits.bundles.upload":
                return Request(path, {"versionCode": 7})
            if path == "edits.commit":
                return Request(path, error=COMMIT_ERROR)
            return Chain(path) if path in ("edits", "edits.bundles", "edits.deobfuscationfiles", "edits.tracks") else Request(path)
        return call

module("httplib2", Http=lambda **kw: None, HttpLib2Error=type("HttpLib2Error", (Exception,), {}))
module("google")
module("google.oauth2")
module("google.oauth2.service_account", Credentials=types.SimpleNamespace(from_service_account_info=lambda info, scopes=None: object()))
module("google_auth_httplib2", AuthorizedHttp=lambda creds, http=None: None)
module("googleapiclient")
module("googleapiclient.discovery", build=lambda *a, **k: Chain())
module("googleapiclient.http", MediaFileUpload=lambda *a, **k: None)
module("googleapiclient.errors", HttpError=HttpError)
exec(compile(open(os.environ["PUBLISHER_SOURCE"]).read(), "publisher", "exec"), {"__name__": "__main__"})
'''


def run_publisher(error: dict) -> tuple[int, dict[str, str], str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "publisher.py").write_text(heredoc_python(), encoding="utf-8")
        (tmp_path / "driver.py").write_text(FAKES, encoding="utf-8")
        (tmp_path / "app.aab").write_bytes(b"aab")
        (tmp_path / "mapping.txt").write_text("m", encoding="utf-8")
        github_env = tmp_path / "github_env"
        github_output = tmp_path / "github_output"
        summary = tmp_path / "summary.md"
        for path in (github_env, github_output, summary):
            path.write_text("", encoding="utf-8")
        env = {
            "PATH": os.environ["PATH"],
            "PLAY_SERVICE_ACCOUNT_JSON": "{}",
            "PACKAGE_NAME": "com.example.app",
            "AAB_PATH": str(tmp_path / "app.aab"),
            "MAPPING_FILE": str(tmp_path / "mapping.txt"),
            "TRACKS_JSON": json.dumps([{"track": "internal", "status": "completed"}]),
            "FAKE_COMMIT_ERROR": json.dumps(error),
            "PUBLISHER_SOURCE": str(tmp_path / "publisher.py"),
            "GITHUB_ENV": str(github_env),
            "GITHUB_OUTPUT": str(github_output),
            "GITHUB_STEP_SUMMARY": str(summary),
        }
        proc = subprocess.run(
            [sys.executable, "-I", str(tmp_path / "driver.py")],
            env=env, capture_output=True, text=True, cwd=tmp, timeout=60,
        )
        parsed = dict(
            line.split("=", 1) for line in github_env.read_text(encoding="utf-8").splitlines() if "=" in line
        )
        return proc.returncode, parsed, summary.read_text(encoding="utf-8"), proc.stdout + proc.stderr


# 1. The daily quota defers: exit 0, every "Play accepted it" step suppressed, retry-after reported.
code, env_out, summary, log = run_publisher({"status": 403, "message": "Daily save quota exceeded."})
assert code == 0, log
assert env_out.get("PLAY_DEFERRED") == "true", env_out
assert env_out.get("PUBLISH_PLAY") == "false" and env_out.get("PUBLISH_GITHUB_RELEASE") == "false", env_out
# The Illumera github_built_release_always path is gated by its own flag: it must not publish either.
assert env_out.get("PUBLISH_BUILT_GITHUB_RELEASE") == "false", env_out
assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", env_out.get("PLAY_RETRY_AFTER", "")), env_out
assert "daily save quota exceeded" in summary.lower() and "retry after" in summary.lower(), summary
assert "::warning title=Play daily save quota exceeded::" in log, log

# 2. A Retry-After header wins over the midnight-Pacific default.
code, env_out, _summary, log = run_publisher(
    {"status": 403, "message": "Daily save quota exceeded.", "headers": {"retry-after": "3600"}}
)
assert code == 0, log
assert env_out["PLAY_DEFERRED"] == "true", env_out

# 3. Any other 403 (here: permission denied) is still a failure and defers nothing.
code, env_out, _summary, log = run_publisher({"status": 403, "message": "The caller does not have permission"})
assert code != 0, log
assert "PLAY_DEFERRED" not in env_out, env_out

# 4. The supersede check, against a fake `gh`.
SHELL = supersede_shell()


def run_supersede(compare_json: str, event: str = "push", ref: str = "main") -> str:
    with tempfile.TemporaryDirectory() as tmp:
        bindir = Path(tmp) / "bin"
        bindir.mkdir()
        gh = bindir / "gh"
        gh.touch()
        # The script calls `gh api <path> --jq <expr>`; the fake only needs to honour --jq for compare.
        gh.write_text(
            "#!/usr/bin/env bash\n"
            'path="$2"\n'
            'if [ "$path" = "repos/o/r" ]; then echo main; exit 0; fi\n'
            'jqexpr=""; while [ $# -gt 0 ]; do if [ "$1" = "--jq" ]; then jqexpr="$2"; fi; shift; done\n'
            'printf "%s" "$COMPARE" | jq -r "$jqexpr"\n',
            encoding="utf-8",
        )
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        out = Path(tmp) / "out"
        out.write_text("", encoding="utf-8")
        script = Path(tmp) / "check.sh"
        script.write_text(SHELL + '\necho "superseded=$superseded" >> "$OUT"\n', encoding="utf-8")
        env = {
            "PATH": f"{bindir}:{os.environ['PATH']}",
            "COMPARE": compare_json,
            "OUT": str(out),
            "TARGET_REPOSITORY": "o/r",
            "TARGET_SHA": "abc",
            "TARGET_REF_NAME": ref,
            "TARGET_REF_TYPE": "branch",
            "TARGET_EVENT_NAME": event,
        }
        proc = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr
        return out.read_text(encoding="utf-8").strip()


def compare(status, files, messages):
    return json.dumps({
        "status": status,
        "files": [{"filename": name} for name in files],
        "commits": [{"commit": {"message": message}} for message in messages],
    })


newer_code = compare("ahead", ["app/src/Main.kt"], ["feat: change"])
newer_bookkeeping = compare("ahead", ["version.properties"], ["feat: nothing"])
same = compare("identical", [], [])
assert run_supersede(newer_code) == "superseded=true"
assert run_supersede(newer_bookkeeping) == "superseded=false"
assert run_supersede(same) == "superseded=false"
assert run_supersede(newer_code, event="workflow_dispatch") == "superseded=false"
assert run_supersede(newer_code, ref="feature") == "superseded=false"
# A newer [skip ci] commit never starts a replacement run (pushDropReason / dispatch_request drop it),
# so it must not supersede, whatever files it changes; neither must any other skip token, in any case.
for token in ("[skip ci]", "[CI Skip]", "[no ci]", "[skip actions]", "[actions skip]"):
    assert run_supersede(compare("ahead", ["app/src/Main.kt"], [f"chore: x {token}"])) == "superseded=false", token
# A skipped commit after an eligible one: the eligible commit still gets its own run.
assert run_supersede(compare("ahead", ["a.kt", "b.kt"], ["feat: x", "chore(version): 1 [skip ci]"])) == "superseded=true"
# The same shell body guards the late re-check just before publishing: a [skip ci] commit arriving
# during the build must not cancel the publish either.
late_start = text.index("      - name: Skip Play publish for a superseded commit")
late_run = text.index("        run: |\n", late_start) + len("        run: |\n")
late_end = text.index('\n          if [ "$superseded" = true ]; then', late_run)
late_block = text[late_end:text.index("      - name: Publish bundle to configured Play tracks")]
for flag in ("PUBLISH_PLAY=false", "PUBLISH_GITHUB_RELEASE=false", "PUBLISH_BUILT_GITHUB_RELEASE=false"):
    assert f'echo "{flag}"' in late_block, f"late supersede check must set {flag}"
assert textwrap.dedent(text[late_run:late_end]) == SHELL, "late re-check must run the same predicate as the early check"

# The skip tokens are one list in three places; the three must not drift.
sys.path.insert(0, str(ROOT / "scripts"))
from dispatch_request import CI_SKIP_TOKENS  # noqa: E402
worker_src = (ROOT / "worker/src/event-filter.js").read_text(encoding="utf-8")
worker_tokens = tuple(re.findall(r'"(\[[a-z ]+\])"', re.search(r"CI_SKIP_TOKENS = \[(.*?)\]\;", worker_src, re.S).group(0)))
assert worker_tokens == CI_SKIP_TOKENS, (worker_tokens, CI_SKIP_TOKENS)
shell_alt = re.search(r'test\("\\\\\[\((.*?)\)\\\\\]"\)', SHELL)
assert shell_alt, "supersede shell must carry the skip-token regex"
assert tuple(f"[{t}]" for t in shell_alt.group(1).split("|")) == CI_SKIP_TOKENS, shell_alt.group(1)

# 5. Central action references are pinned by SHA to the current action tree.
action_ref = re.compile(r"HereLiesAz/workflows/\.github/actions/([a-z0-9-]+)@([^\s#]+)")
problems = []
for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
    for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for match in action_ref.finditer(line):
            name, ref = match.groups()
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                problems.append(f"{workflow.name}:{number}: {name}@{ref} is not pinned by SHA")
                continue
            # The action directory AND every file it runs from outside that directory
            # ($GITHUB_ACTION_PATH/../... resolves inside the PINNED checkout, not the workflow's).
            action_yml = (ROOT / ".github/actions" / name / "action.yml").read_text(encoding="utf-8")
            paths = {f".github/actions/{name}"}
            for rel in re.findall(r"GITHUB_ACTION_PATH/((?:\.\./)+[^\s\"'`)]+)", action_yml):
                resolved = os.path.normpath(os.path.join(".github/actions", name, rel))
                paths.add(resolved)
            for path in sorted(paths):
                have = subprocess.run(["git", "rev-parse", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True)
                want = subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True)
                if have.returncode != 0:
                    # A pin that cannot be resolved cannot be shown fresh. The validate job fetches
                    # full history; a shallow clone must fail here, not weaken the check.
                    problems.append(f"{workflow.name}:{number}: cannot resolve {path} at {name}@{ref[:12]} (fetch full history)")
                elif have.stdout.strip() != want.stdout.strip():
                    problems.append(f"{workflow.name}:{number}: {name}@{ref[:12]} is stale; {path} changed since that commit")
assert not problems, "\n".join(problems)

print("play publish resilience tests passed")

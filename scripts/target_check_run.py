#!/usr/bin/env python3
"""Mirror central run results onto the target commit as GitHub Check Runs.

Commit statuses (posted by central_check_start / central_check_finish) stay the
authoritative signal and keep target trackers working. Check Runs are added on
top because agents and integrations watching a repository wake on `check_run`
events, not `status` events. A Check Run also carries a readable summary: on
failure, the failed jobs, their failed steps and a log tail of the first one.

Check Runs can only be written with a GitHub App installation token, so each
step mints one from GH_APP_ID / GH_PRIVATE_KEY. Every step is best effort:
`continue-on-error`, and the script itself only ever warns.

Usage (re-apply to every committed central workflow; idempotent):

    python scripts/target_check_run.py .github/workflows/*.yml
"""
from __future__ import annotations

import re
import sys
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

APP_TOKEN_ACTION = "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1"
MINT_STEP_NAME = "Mint target check token"
POST_STEP_NAME = "Post target check run"

_CHECK_SCRIPT = r'''set +e
warn() { echo "::warning::Target check run skipped: $1"; exit 0; }
[[ -n "${TARGET_REPOSITORY:-}" && -n "${TARGET_CHECK_SHA:-}" ]] || warn "no target commit"
title="$CHECK_NAME"
text=""
if [[ "$CHECK_PHASE" == "start" ]]; then
  body="$(jq -n --arg name "$CHECK_NAME" --arg sha "$TARGET_CHECK_SHA" --arg url "$DETAILS_URL" --arg ext "$GITHUB_RUN_ID" \
    '{name:$name,head_sha:$sha,status:"in_progress",details_url:$url,external_id:$ext,output:{title:$name,summary:("Running in HereLiesAz/workflows: " + $url)}}')"
else
  if [[ "$FAILED" == "true" ]]; then
    conclusion="failure"
    jobs="$(GH_TOKEN="$RUN_READ_TOKEN" gh api --paginate "repos/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}/attempts/${GITHUB_RUN_ATTEMPT}/jobs" --jq '.jobs[]' 2>/dev/null | jq -s '.')"
    [[ -n "$jobs" ]] || jobs="[]"
    failed="$(jq -r '[.[] | select(.conclusion == "failure" or .conclusion == "cancelled")
      | "- **\(.name)** (\(.conclusion)): " + ([.steps[]? | select(.conclusion == "failure") | .name] | join(", ") | if . == "" then "no failed step reported" else . end)
      + " — [log](\(.html_url))"] | join("\n")' <<<"$jobs")"
    first_id="$(jq -r '[.[] | select(.conclusion == "failure")][0].id // empty' <<<"$jobs")"
    if [[ -n "$first_id" ]]; then
      tail_log="$(GH_TOKEN="$RUN_READ_TOKEN" gh api "repos/${GITHUB_REPOSITORY}/actions/jobs/${first_id}/logs" 2>/dev/null \
        | sed -E 's/^[0-9T:.-]+Z //' | grep -v '^##\[group\]\|^##\[endgroup\]' | tail -n 60)"
      [[ -n "$tail_log" ]] && text="$(printf 'Last lines of the first failed job:\n\n~~~text\n%s\n~~~\n' "${tail_log:0:60000}")"
    fi
    summary="$(printf 'Central run failed: %s\n\n%s\n' "$DETAILS_URL" "${failed:-No failed job reported.}")"
    title="$CHECK_NAME failed"
  else
    conclusion="success"
    summary="Central run succeeded: $DETAILS_URL"
  fi
  body="$(jq -n --arg name "$CHECK_NAME" --arg sha "$TARGET_CHECK_SHA" --arg url "$DETAILS_URL" --arg ext "$GITHUB_RUN_ID" \
    --arg conclusion "$conclusion" --arg title "$title" --arg summary "${summary:0:65000}" --arg text "$text" \
    '{name:$name,head_sha:$sha,status:"completed",conclusion:$conclusion,details_url:$url,external_id:$ext,output:({title:$title,summary:$summary} + (if $text == "" then {} else {text:$text} end))}')"
fi
# Each phase posts its own Check Run under the same name; GitHub shows the latest one,
# so the finish phase needs no id handed over from the start job.
gh api --method POST "repos/${TARGET_REPOSITORY}/check-runs" --input - <<<"$body" >/dev/null \
  || echo "::warning::Target check run skipped: GitHub refused the check run"

# Release/deploy failures also go to one open issue per workflow: opened on the
# first failure, commented on each repeat. Successes never touch issues.
[[ "$CHECK_PHASE" == "finish" && "${FILE_ISSUES:-}" == "true" && "${conclusion:-}" == "failure" ]] || exit 0
label="central-run-failure"
issue_title="Central run failing: $CHECK_NAME"
issue="$(gh api "repos/${TARGET_REPOSITORY}/issues?state=open&labels=${label}&per_page=100" 2>/dev/null \
  | jq -r --arg t "$issue_title" '[.[] | select(.title == $t)][0].number // empty')"
report="$(printf '%s\n\nCommit: %s\n\n%s\n' "$summary" "$TARGET_CHECK_SHA" "$text")"
if [[ -n "$issue" ]]; then
  gh api --method POST "repos/${TARGET_REPOSITORY}/issues/${issue}/comments" -f body="$report" >/dev/null \
    || warn "could not comment on issue #$issue"
else
  gh api --method POST "repos/${TARGET_REPOSITORY}/labels" -f name="$label" -f color="000000" \
    -f description="A release or deploy run in HereLiesAz/workflows failed for this repository." >/dev/null 2>&1
  gh api --method POST "repos/${TARGET_REPOSITORY}/issues" -f title="$issue_title" -f body="$report" -f "labels[]=$label" >/dev/null \
    || warn "could not open a failure issue"
fi
'''


# Workflows whose failures also open an issue in the target repository.
ISSUE_WORKFLOW_RE = re.compile(r"release|deploy", re.I)


def target_check_steps(phase: str, file_issues: bool = False) -> list[dict]:
    """The two steps appended to central_check_start (phase=start) or central_check_finish (phase=finish)."""
    if phase not in {"start", "finish"}:
        raise ValueError(f"unknown phase {phase!r}")
    env = {
        "GH_TOKEN": "${{ steps.target-check-token.outputs.token }}",
        "RUN_READ_TOKEN": "${{ secrets.GH_TOKEN }}",
        "CHECK_PHASE": phase,
        "CHECK_NAME": "${{ inputs.target_workflow_name || inputs.source_workflow_path }}",
        "DETAILS_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
    }
    if phase == "finish":
        env["FAILED"] = "${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}"
        if file_issues:
            env["FILE_ISSUES"] = "true"
    return [
        {
            "name": MINT_STEP_NAME,
            "id": "target-check-token",
            "continue-on-error": True,
            "uses": APP_TOKEN_ACTION,
            "with": {
                "app-id": "${{ secrets.GH_APP_ID }}",
                "private-key": "${{ secrets.GH_PRIVATE_KEY }}",
                "owner": "HereLiesAz",
            },
        },
        {
            "name": POST_STEP_NAME,
            "if": "${{ always() && steps.target-check-token.outputs.token != '' }}",
            "continue-on-error": True,
            "env": env,
            "shell": "bash",
            "run": _CHECK_SCRIPT,
        },
    ]


def add_target_check_steps(jobs: dict, file_issues: bool = False) -> bool:
    """Append (or refresh) the check-run steps on a compiled workflow's reporting jobs. Returns True if changed."""
    changed = False
    for job_id, phase in (("central_check_start", "start"), ("central_check_finish", "finish")):
        job = jobs.get(job_id)
        if not isinstance(job, dict):
            continue
        steps = [s for s in (job.get("steps") or []) if not (isinstance(s, dict) and s.get("name") in {MINT_STEP_NAME, POST_STEP_NAME})]
        new_steps = steps + target_check_steps(phase, file_issues)
        if list(job.get("steps") or []) != new_steps:
            job["steps"] = new_steps
            changed = True
    return changed


SECRET_DECLARATIONS = {
    "GH_APP_ID": "GitHub App that writes the Check Run mirroring this run onto the target commit.",
    "GH_PRIVATE_KEY": "Private key of that GitHub App, used to mint its installation token.",
}


def add_preflight_checks(jobs: dict) -> bool:
    """Workflows with a policy_secret_preflight job must check the App secrets there too."""
    preflight = jobs.get("policy_secret_preflight")
    if not isinstance(preflight, dict) or not preflight.get("steps"):
        return False
    env = preflight.setdefault("env", {})
    step = preflight["steps"][0]
    run = str(step.get("run") or "")
    changed = False
    for name, purpose in SECRET_DECLARATIONS.items():
        if f"REQUIRED_{name}" not in env:
            env[f"REQUIRED_{name}"] = f"${{{{ secrets.{name} }}}}"
            changed = True
        if f"Missing required secret {name} " not in run:
            run = run.rstrip("\n") + (
                f'\ntest -n "${{REQUIRED_{name}:-}}" || {{\n'
                f'  echo "::error::Missing required secret {name} — {purpose}"\n'
                f"  exit 1\n}}\n"
            )
            changed = True
    if changed:
        step["run"] = LiteralScalarString(run)
    return changed


def declare_secrets(text: str) -> str:
    """Workflows that declare their secrets (`# required-secret:` headers) must declare the App's too."""
    lines = text.splitlines(keepends=True)
    declared = [i for i, line in enumerate(lines) if line.startswith("# required-secret:")]
    if not declared:
        return text
    missing = [f"# required-secret: {name} | {purpose}\n" for name, purpose in SECRET_DECLARATIONS.items()
               if not any(lines[i].startswith(f"# required-secret: {name} ") for i in declared)]
    return "".join(lines[: declared[-1] + 1] + missing + lines[declared[-1] + 1 :])


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def main(paths: list[str]) -> int:
    y = _yaml()
    for raw in paths:
        path = Path(raw)
        text = path.read_text()
        if "central_check_finish:" not in text:
            continue
        doc = y.load(text)
        updated = text
        jobs = doc.get("jobs") or {}
        steps_changed = add_target_check_steps(jobs, bool(ISSUE_WORKFLOW_RE.search(path.name)))
        if add_preflight_checks(jobs) or steps_changed:
            out = StringIO()
            y.dump(doc, out)
            updated = out.getvalue()
        updated = declare_secrets(updated)
        if updated == text:
            continue
        path.write_text(updated)
        print(f"updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

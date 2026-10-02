#!/usr/bin/env python3
"""Render the ci-status dashboard (README.md) from the ledger written by worker/src/ci-status.js.

Usage: python scripts/render_ci_status.py <ci-status checkout>
Reads <dir>/repositories/*.json, writes <dir>/README.md. Pure; no network.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ICONS = {
    "success": "✅", "failure": "❌", "cancelled": "⏹", "timed_out": "⌛",
    "action_required": "✋", "skipped": "⏭", "neutral": "◻", "stale": "◻", "startup_failure": "❌",
}


def run_state(run: dict) -> str:
    if run.get("status") == "completed":
        conclusion = str(run.get("conclusion") or "unknown")
        return f"{ICONS.get(conclusion, '❔')} {conclusion}"
    jobs = run.get("jobs") or {}
    done = sum(1 for job in jobs.values() if job.get("status") == "completed")
    progress = f" ({done}/{len(jobs)} jobs)" if jobs else ""
    return f"⏳ {run.get('status') or 'queued'}{progress}"


def cell(text: object) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def render(ledgers: list[dict]) -> str:
    rows = []
    for ledger in sorted(ledgers, key=lambda item: str(item.get("repository", {}).get("full_name", "")).casefold()):
        name = ledger.get("repository", {}).get("full_name", "")
        for path, workflow in sorted((ledger.get("workflows") or {}).items()):
            runs = workflow.get("runs") or []
            if not runs:
                continue
            run = runs[0]
            link = f"[#{run.get('run_number') or run.get('run_id')}]({run['html_url']})" if run.get("html_url") else f"#{run.get('run_id')}"
            summary = "; ".join(
                f"{job}: {report.get('summary')}"
                for job, report in sorted((run.get("reports") or {}).items())
                if report.get("summary")
            )
            rows.append(
                f"| [{cell(name)}](https://github.com/{name}) | {cell(workflow.get('name') or path)} | {run_state(run)} "
                f"| {link} | {cell(run.get('branch'))} | `{str(run.get('sha') or '')[:7]}` | {cell(run.get('updated_at'))} | {cell(summary)} |"
            )
    lines = [
        "# CI status",
        "",
        "CI runs in each project's own repository. This page only records what those runs report",
        "(webhook `workflow_run`/`workflow_job`, plus optional `ci-report` steps). Latest run per workflow;",
        "full history of the last 20 runs is in `repositories/<repository_id>.json`.",
        "",
        "| Repository | Workflow | State | Run | Branch | Commit | Updated | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
    ]
    if not rows:
        lines.insert(-1, "_No CI runs reported yet._")
    return "\n".join(lines)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    ledgers = []
    for file in sorted((root / "repositories").glob("*.json")):
        try:
            ledgers.append(json.loads(file.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            print(f"::warning::Skipping unreadable ledger {file.name}: {exc}")
    (root / "README.md").write_text(render(ledgers), encoding="utf-8")
    print(f"Rendered {len(ledgers)} repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

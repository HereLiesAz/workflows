#!/usr/bin/env python3
"""Fail if a scripts/test_*.py is not actually run by validate-controller.yml.

The test_*.py files are plain assert scripts that pytest cannot discover, so one
that is left out of the workflow never runs. A text search for its path is not
enough: a step with `if: ${{ false }}`, or a commented-out `run:` line, still
contains it. This parses the workflow and requires an enabled step whose `run`
is exactly `python scripts/<name>.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/validate-controller.yml"

# Conditions that leave a step running whenever the job does.
ALWAYS_ENABLED = {None, "", "always()", "${{ always() }}", "success()", "${{ success() }}", "true", "${{ true }}"}


def runnable_commands(workflow: dict) -> set[str]:
    """The `run` commands of steps that are not disabled by an `if:`."""
    commands: set[str] = set()
    for job in (workflow.get("jobs") or {}).values():
        if not isinstance(job, dict) or str(job.get("if", "")).strip() in {"false", "${{ false }}"}:
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict) or "run" not in step:
                continue
            condition = step.get("if")
            if isinstance(condition, str):
                condition = condition.strip()
            if condition not in ALWAYS_ENABLED:
                continue
            commands.add(str(step["run"]).strip())
    return commands


def unwired(workflow: dict, tests: list[str]) -> list[str]:
    commands = runnable_commands(workflow)
    return [test for test in tests if f"python {test}" not in commands]


def main() -> int:
    workflow = YAML(typ="safe").load(WORKFLOW.read_text(encoding="utf-8"))
    tests = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "scripts").glob("test_*.py"))
    missing = unwired(workflow, tests)
    for test in missing:
        print(f"::error::{test} is not run by an enabled step of validate-controller.yml", file=sys.stderr)
    if not missing:
        print(f"all {len(tests)} regression scripts are wired in")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

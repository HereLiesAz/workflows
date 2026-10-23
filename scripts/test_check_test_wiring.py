#!/usr/bin/env python3
"""check_test_wiring must not accept a disabled, commented-out or merely mentioned step."""
from __future__ import annotations

from check_test_wiring import unwired


def wf(*steps):
    return {"jobs": {"validate": {"steps": list(steps)}}}


T = "scripts/test_example.py"
assert unwired(wf({"run": f"python {T}"}), [T]) == []
assert unwired(wf({"name": "x", "if": "${{ always() }}", "run": f"python {T}"}), [T]) == []
assert unwired(wf({"run": "python scripts/test_other.py"}), [T]) == [T]            # not wired at all
assert unwired(wf({"if": "${{ false }}", "run": f"python {T}"}), [T]) == [T]       # disabled
assert unwired(wf({"if": "github.event_name == 'push'", "run": f"python {T}"}), [T]) == [T]   # conditional
assert unwired(wf({"run": f"python {T} --extra"}), [T]) == [T]                      # different command
assert unwired(wf({"run": f"echo python {T}"}), [T]) == [T]                         # only mentioned
assert unwired({"jobs": {"validate": {"if": "false", "steps": [{"run": f"python {T}"}]}}}, [T]) == [T]
assert unwired({}, [T]) == [T]
print("test wiring check ok")

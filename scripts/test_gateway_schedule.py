#!/usr/bin/env python3
"""The gateway's schedule must be exactly the union of active registered crons.

A missing cron means that workflow never fires; an unused one is warned about.
"""
from __future__ import annotations

import json
from pathlib import Path

from ruamel.yaml import YAML

from dispatch_schedule import schedule_crons

ROOT = Path(__file__).resolve().parents[1]

registered: set[str] = set()
for manifest_path in sorted((ROOT / "registry").glob("*/manifest.json")):
    for entry in (json.loads(manifest_path.read_text(encoding="utf-8")).get("workflows") or {}).values():
        if isinstance(entry, dict) and entry.get("status") == "active" and entry.get("registry_source"):
            source = ROOT / entry["registry_source"]
            if source.is_file():
                registered.update(schedule_crons(source))

gateway = YAML(typ="safe").load((ROOT / ".github/workflows/gateway.yml").read_text(encoding="utf-8"))
on_value = gateway.get("on", gateway.get(True))
declared = {str(item["cron"]).strip() for item in on_value["schedule"]}

# A missing cron means a registered workflow never fires: fail. An unused one costs only a tick that
# exits before doing anything, and must exist briefly while a new scheduled workflow is being
# registered (the cron lands before the sync that registers it): warn.
missing = sorted(registered - declared)
assert not missing, f"gateway schedule is missing registered cron(s): {missing}"
for cron in sorted(declared - registered):
    print(f"warning: gateway cron {cron!r} has no active registered workflow; remove it once nothing needs it")
print(f"gateway schedule covers {len(registered)} registered cron(s)")

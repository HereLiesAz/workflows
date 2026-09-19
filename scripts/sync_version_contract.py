#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

try:
    from .sync_repository_catalog import GitHub
    from .sync_repository import _ensure_version_contract
except ImportError:
    from sync_repository_catalog import GitHub
    from sync_repository import _ensure_version_contract


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce major.minor.patch.build on one repository.")
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()

    gh = GitHub(os.environ.get("GH_TOKEN", ""))
    repo = gh.repo(args.repository)
    if bool(repo.get("archived")):
        print(json.dumps({"repository": args.repository, "status": "archived", "changed": False}))
        return 0

    default_branch = str(repo["default_branch"])
    result = _ensure_version_contract(
        gh,
        args.repository,
        default_branch,
        dry_run=False,
    )
    print(json.dumps(
        {
            "repository": args.repository,
            "default_branch": default_branch,
            "status": "enforced",
            **result,
        },
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

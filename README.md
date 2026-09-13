# workflows

Central shared workflow catalog and secure execution gateway for repositories owned by `HereLiesAz`.

This repository exists to reuse **workflow implementations as well as credentials**. Target repositories keep lightweight trigger/proxy workflows for centrally executed automation. Canonical implementations live here and can be reused by multiple repositories. Workflows that are genuinely repository-bound remain local.

## Architecture

```text
Target repository event
        │
        ▼
secretless OIDC proxy
        │
        ▼
Cloudflare Worker · workflows.hereliesaz.workers.dev
        │
        ▼
central gateway
        │
        ▼
shared catalog workflow
        │
        ▼
target operation + commit status
```

The Worker verifies GitHub OIDC identity and immutable repository ownership before dispatching the central gateway. The gateway validates the registered workflow binding and source hash. Shared workflows re-validate the target repository before privileged execution.

Runtime results are reported back to the target SHA using **commit statuses**, not Check Runs.

## Adding another repository

See **[Repository onboarding](docs/REPOSITORY_ONBOARDING.md)** for the complete conversion procedure, safety rules, classification model, smoke-test process, rollback procedure, and the checklist we will use for every repository.

The normal migration flow is:

1. inventory the target repository's workflows, variables, local actions, and scripts;
2. ensure the central controller has the required repository access and workflow credentials;
3. run **Sync repository workflows** with `dry_run: true`;
4. review every workflow classification and identify obsolete automation;
5. add repository policy for workflows that should be removed rather than migrated;
6. run the sync with `dry_run: false`;
7. inspect the target proxies/local workflows and central registry bindings;
8. exercise at least one centralized workflow end to end;
9. remove duplicated target credentials only after runtime verification succeeds.

The real sync automatically creates or updates the target repository variable `WORKFLOWS_GATEWAY_URL` with:

```text
https://workflows.hereliesaz.workers.dev
```

## Workflow catalog model

The synchronizer uses four outcomes:

| Outcome | Purpose |
| --- | --- |
| Curated catalog | Known canonical implementations such as Jules Dispatch, Glee, Context Backup, and Clear Cache |
| Content-addressed catalog | Other centrally safe workflow logic, deduplicated by implementation hash across repositories |
| Library | `workflow_call` helpers that stay available as reusable source components |
| Local | Repository-bound workflows whose behavior would change or become unsafe if executed from this repository |

Current curated implementations are:

- `.github/workflows/catalog-jules-dispatch.yml`
- `.github/workflows/catalog-jules-glee.yml`
- `.github/workflows/catalog-context-backup.yml`
- `.github/workflows/catalog-clear-cache.yml`

Per-repository source state and bindings are stored under `registry/<repository-id>/`. Legacy per-repository `absorbed-<repo-id>-*.yml` executors are garbage-collected after successful catalog binding.

## Repository-local scripts and actions

Project-specific `scripts/` and local composite actions stay in their target repositories. Central jobs that need them check out the originating repository at the originating SHA, keeping those dependencies version-locked to the target commit.

The synchronizer blocks a workflow if it tries to use a repo-local script/action before a full target-repository checkout.

Dependencies that are part of a **shared workflow implementation** should live here alongside the shared workflow instead of being copied into every target repository.

## Controller workflows

- `sync-repository.yml` — manually scans and binds one target repository to the shared catalog.
- `gateway.yml` — receives verified dispatches from the Worker and routes them to the registered shared workflow.
- `validate-controller.yml` — validates controller code and generated workflow behavior.

Always run a **dry sync first** for a new repository. A repository is not considered converted until every classification has been reviewed and at least one centralized runtime path has been proven end to end.
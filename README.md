# workflows

Central shared workflow catalog and secure execution gateway for repositories owned by `HereLiesAz`.

This repository exists to reuse **workflow implementations as well as credentials**. Centrally managed target repositories do not need controller-generated workflow files. Repository events arrive through one signed GitHub webhook, the gateway matches those events against the registered original `on:` contracts, and canonical implementations execute here. Workflows that are not yet safe to centralize remain local only until their blocker is resolved.

## Architecture

```text
Target repository event
        │
        ▼
GitHub repository webhook (HMAC signed)
        │
        ▼
Cloudflare Worker · workflows.hereliesaz.workers.dev
        │
        ▼
central gateway
        │ matches the event against registered original on: rules
        ▼
shared/catalog workflow
        │
        ▼
target operation + commit status
```

The central sync registers one repository webhook through the Worker. The Worker verifies GitHub's webhook signature and immutable repository ownership before dispatching the central gateway. The gateway validates registry bindings and routes only workflows whose original trigger, branch/action filters, and path filters match the delivered event. Shared workflows re-validate the target repository before privileged execution.

The legacy OIDC `/dispatch` endpoint is retained only while old proxies are being removed; it is not the steady-state trigger transport.

Runtime results are reported back to the target SHA using **commit statuses**, not Check Runs. Each target keeps a tracker per centralized workflow at its original path, listing what it uses and mirroring each run's result into the target's Actions tab.

## Workflow policy and repository templates

New workflow implementations must be submitted to this repository and generalized for reuse before they are allowed into a target repository. See **[Generalized workflow policy](docs/WORKFLOW_POLICY.md)**.

Release/version semantics are also centralized. See **[Central release and version policy](docs/RELEASE_VERSIONING.md)**. Four-part builds keep immutable exact-build tags while their artifacts are grouped under one patch-level GitHub Release.

Repository starters:

- `HereLiesAz/workflows-starter-template` — general/meta repository
- `HereLiesAz/android-app-template` — Android + Compose
- `HereLiesAz/compose-multiplatform-template` — Compose Multiplatform with Android and desktop entry points
- `HereLiesAz/react-app-template` — React + TypeScript + Vite
- `HereLiesAz/gradle-library-template` — Kotlin/JVM library for GitHub Packages and JitPack

Each template carries `.github/workflow-request.yml`, a non-executable menu/request file. Executable implementations stay centralized here.

## Adding another repository

See **[Repository onboarding](docs/REPOSITORY_ONBOARDING.md)** for the complete conversion procedure, safety rules, classification model, smoke-test process, rollback procedure, and the checklist we will use for every repository.

The normal migration flow is:

1. inventory the target repository's workflows, variables, local actions, and scripts;
2. ensure the central controller has the required repository access and workflow credentials;
3. run **Sync repository workflows** with `dry_run: true`;
4. review every workflow classification and identify obsolete automation;
5. add repository policy for workflows that should be removed rather than migrated;
6. run the sync with `dry_run: false`;
7. verify the target has a tracker for every centralized workflow, no dispatching proxy, and inspect any intentionally local blockers;
8. exercise at least one centralized workflow end to end through the repository webhook;
9. remove duplicated target credentials only after runtime verification succeeds.

The real sync registers or refreshes the target repository webhook at `https://workflows.hereliesaz.workers.dev/webhook` before removing any old proxy, so a failed gateway registration leaves the target untouched.

## Workflow catalog model

The synchronizer uses four outcomes:

| Outcome | Purpose |
| --- | --- |
| Curated catalog | Known canonical implementations such as Jules Dispatch, Glee, Context Backup, and Clear Cache |
| Reviewed semantic catalog | Workflows that accomplish the same job share one named implementation after semantic review; hashes are only change-detection guards |
| Library | `workflow_call` helpers that stay available as reusable source components |
| Local | Repository-bound workflows whose behavior would change or become unsafe if executed from this repository |

Current curated implementations are:

- `.github/workflows/catalog-jules-dispatch.yml`
- `.github/workflows/catalog-jules-glee.yml`
- `.github/workflows/catalog-context-backup.yml`
- `.github/workflows/catalog-clear-cache.yml`

Per-repository source state and bindings are stored under `registry/<repository-id>/`. Equivalent behavior is bound to one purpose-level workflow; repository-specific executors are kept only when the behavior is genuinely unique or still awaiting semantic review.

## Repository-local scripts and actions

Project-specific `scripts/` and local composite actions stay in their target repositories. Central jobs that need them check out the originating repository at the originating SHA, keeping those dependencies version-locked to the target commit.

The synchronizer blocks a workflow if it tries to use a repo-local script/action before a full target-repository checkout.

Dependencies that are part of a **shared workflow implementation** should live here alongside the shared workflow instead of being copied into every target repository.

The same rule applies to cross-repository release policy. Shared release families use the reusable
`four-part-version` and `minor-grouped-release` actions here rather than copying version/tag/release
shell logic into target repositories.

## Controller workflows

- `sync-repository.yml` — manually scans and binds one target repository to the shared catalog.
- `gateway.yml` — receives verified dispatches from the Worker and routes them to the registered shared workflow.
- `validate-controller.yml` — validates controller code and generated workflow behavior.

Always run a **dry sync first** for a new repository. A repository is not considered converted until every classification has been reviewed and at least one centralized runtime path has been proven end to end.
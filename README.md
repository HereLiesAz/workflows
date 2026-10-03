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

The central sync registers one repository webhook through the Worker. The Worker verifies GitHub's webhook signature and immutable repository ownership before dispatching the central gateway. It then forwards an event only when some **active** registered workflow of that repository is triggered by that event name (`push` is always forwarded for a registered repository, because a push can request a re-sync); every other event, e.g. `workflow_run`, `release`, `check_*`, or anything from an unregistered repository, is dropped with `202 {ok: true, ignored: true, reason}` and never costs a gateway run. That decision uses `worker/src/event-consumers.js`, generated from `registry/` by `scripts/generate_event_consumers.py` (see [Repository onboarding](docs/REPOSITORY_ONBOARDING.md#worker-event-filter)). The gateway validates registry bindings and routes only workflows whose original trigger, branch/action filters, and path filters match the delivered event. Shared workflows re-validate the target repository before privileged execution.

The legacy OIDC `/dispatch` endpoint is retained only while old proxies are being removed; it is not the steady-state trigger transport.

Runtime results are reported back to the target SHA using **commit statuses**, not Check Runs. Each target keeps a tracker per centralized workflow at its original path, listing what it uses. A tracker is one seconds-long job that names the commit status carrying the central result; it never waits on the central run, so it never holds a runner the central run needs.

## CI runs in its own repository

CI is the exception to central execution: every project runs its own CI in its own repository, so fundamental testing is never blocked, queued or delayed by central capacity, the gateway, or this repository's health. The controller only **records** what that CI reports, on the orphan branch [`ci-status`](https://github.com/HereLiesAz/workflows/tree/ci-status) (no workflow files, so its commits start nothing):

~~~text
target CI run (runs in the target repository)
   ├─ workflow_run / workflow_job webhook ─┐     (automatic, no target code)
   └─ optional ci-report step (OIDC) ──────┤     (custom summary/data)
                                           ▼
                          Worker · worker/src/ci-status.js
                                           ▼
           ci-status branch · repositories/<repository_id>.json (last 20 runs, per job progress)
                                           ▼
           ci-status-dashboard.yml (every 15 min) → ci-status/README.md
~~~

- A workflow is **target CI** (`status: local`, `ci: true` in its manifest entry) when it calls `HereLiesAz/workflows/.github/actions/ci-report`, or when the catalog would otherwise bind it to `ci-validation.yml`, whatever its triggers. CI and dependency submission always run from the target repository's own Actions (dependency submission is already a central-execution blocker).
- The sync restores a target CI workflow's original source over its tracker and never blocks a new one under the submission policy. Secrets it references are listed in the entry's `required_secrets`; they must exist in the target repository.
- `scripts/generate_event_consumers.py` lists each repository's target CI under `ci` in the Worker's map; the Worker records those `workflow_run`/`workflow_job` deliveries and never forwards them to the gateway.
- Reporting failures never affect the run: the webhook is out-of-band, and the `ci-report` action turns every error into a warning.

Optional explicit report, as the last step of a CI job:

~~~yaml
permissions:
  contents: read
  id-token: write   # the run's OIDC token authenticates the report; no secret needed
steps:
  # ... build and test ...
  - if: always()
    uses: HereLiesAz/workflows/.github/actions/ci-report@main
    with:
      summary: 128 passed, 0 failed
      data: '{"passed": 128, "failed": 0}'
~~~

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

New public repositories need no action: **Sync repository workflows** runs hourly, registers any repository without a registry entry, and runs its push workflows once so nothing that happened before registration is missed. To run a registered workflow by hand, start **Central workflow gateway** with the repository name and, if it has more than one, the workflow's file or display name.

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
`four-part-version` and `patch-grouped-release` actions here rather than copying version/tag/release
shell logic into target repositories.

## Controller workflows

- `sync-repository.yml` — manually scans and binds one target repository to the shared catalog.
- `gateway.yml` — receives verified dispatches from the Worker and routes them to the registered shared workflow.
- `validate-controller.yml` also redeploys the Worker (`wrangler deploy --config wrangler.jsonc`) on a push to `main` that changes `worker/` or `wrangler.jsonc`, including a regenerated event-consumer map.
- `validate-controller.yml` — validates controller code and generated workflow behavior.
- `ci-status-dashboard.yml` — renders the `ci-status` branch dashboard from what target CI reported.

Always run a **dry sync first** for a new repository. A repository is not considered converted until every classification has been reviewed and at least one centralized runtime path has been proven end to end.
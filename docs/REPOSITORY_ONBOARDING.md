# Repository onboarding

This document is the conversion checklist for binding another `HereLiesAz/*` repository to the centralized workflow catalog in `HereLiesAz/workflows`.

The goal is not merely to centralize secrets. The goal is to reuse workflow implementations. A target repository should keep only the trigger/proxy needed to describe *when* a shared workflow runs, while the reusable implementation lives once in this repository. Workflows that are genuinely repository-bound remain local.

## Architecture

A centralized workflow follows this path:

```text
Target repository event
        │
        ▼
secretless proxy workflow
        │ GitHub OIDC
        ▼
Cloudflare Worker
https://workflows.hereliesaz.workers.dev
        │ verifies owner/repository identity
        ▼
HereLiesAz/workflows · gateway.yml
        │ validates registry binding + source hash
        ▼
shared catalog workflow
        │ uses central secrets and GH_TOKEN
        ▼
target repository operation + commit status
```

The Cloudflare Worker contains only `DISPATCH_TOKEN`. Workflow credentials and service secrets live in `HereLiesAz/workflows`. Target repositories should not keep duplicate Actions secrets after the corresponding workflow has been successfully centralized.

The controller only accepts repositories owned by GitHub user `HereLiesAz` with immutable owner ID `103241502`.

## What is shared and what stays local

The synchronizer classifies each target workflow into one of four outcomes.

| Result | Meaning | Target repository after sync | Central repository |
| --- | --- | --- | --- |
| `catalog` / curated | The workflow matches a known canonical shared implementation | Secretless OIDC proxy | Uses a named `catalog-*.yml` implementation |
| `catalog` / content-addressed | The workflow is safe to execute centrally and has no curated implementation yet | Secretless OIDC proxy | One descriptively named shared workflow with an implementation-hash suffix; identical logic can be reused by multiple repos |
| `library` | The workflow is a `workflow_call` helper/reusable component | Remains in the target repository | Original source is registered for inlining/reference |
| `local` | The workflow is repository-bound or unsafe to execute centrally | Remains/restored locally | Source and blocker reasons are registered, but execution stays in the target repo |

Current curated workflow bindings are:

| Target workflow path | Shared implementation |
| --- | --- |
| `.github/workflows/jules-dispatch.yml` | `.github/workflows/catalog-jules-dispatch.yml` |
| `.github/workflows/jules-glee.yml` | `.github/workflows/catalog-jules-glee.yml` |
| `.github/workflows/backup.yml` | `.github/workflows/catalog-context-backup.yml` |
| `.github/workflows/clear_cache.yml` | `.github/workflows/catalog-clear-cache.yml` |

A workflow is deliberately kept local when central execution would change its meaning. Examples include repository-bound GitHub Pages deployment, dependency-submission actions, labelers that use runner-repository context, or other actions whose API behavior implicitly targets the repository in which the workflow itself is running.

Pure `workflow_call` helpers are treated as libraries rather than standalone central executors because synchronous reusable-workflow outputs cannot be preserved across the Worker boundary.

## Repository-local scripts and actions

Do **not** copy every target repository's `scripts/` directory into this repository.

A shared workflow may still use project-specific files from the target repository. When a centrally executed job contains `actions/checkout`, the compiler rewrites that checkout to the originating target repository and triggering SHA. That keeps project scripts, build files, and local composite actions version-locked to the exact target commit.

The synchronizer blocks a workflow if it uses `scripts/...`, `.github/scripts/...`, or `uses: ./...` before a full target-repository checkout. This prevents a workflow from being marked central when its local dependencies would not exist in the central runner workspace.

If a script or composite action is itself part of the *shared workflow implementation* rather than project-specific code, move that shared dependency into `HereLiesAz/workflows` alongside the curated workflow instead of duplicating it across target repositories.

## Prerequisites before converting a repository

Before running the synchronizer, confirm all of the following:

1. The repository is owned directly by `HereLiesAz`.
2. `GH_TOKEN` in `HereLiesAz/workflows` has access to the target repository and enough permission to read/write workflow files, repository variables, commit statuses, and whatever target operations the shared workflows require.
3. Any workflow-specific secrets used by workflows being centralized already exist in `HereLiesAz/workflows`.
4. The Cloudflare Worker `workflows` is deployed at `https://workflows.hereliesaz.workers.dev` and has the `DISPATCH_TOKEN` Worker secret.
5. The target repository's existing `.github/workflows/`, `.github/actions/`, and workflow-referenced `scripts/` paths have been inventoried before changes are made.
6. Any intentionally obsolete workflows have been identified so they can be disabled through repository policy instead of migrated.

The target repository does **not** need to be given central service secrets. The real sync automatically creates or updates the repository Actions variable `WORKFLOWS_GATEWAY_URL` with the Worker URL.

## Conversion procedure

### 1. Inventory the target repository

Review every file under `.github/workflows/` and note:

- trigger(s)
- secrets referenced
- repository variables referenced
- local reusable workflows (`uses: ./.github/workflows/...`)
- local actions (`uses: ./.github/actions/...` or another `./...` path)
- repo-local scripts called by `run:` steps
- deploy/release behavior
- jobs that use `github.*`, `context.repo`, environments, Pages, dependency submission, or other repository-bound APIs

Also identify duplicated stock/template workflows and obsolete automation before migration. Centralization should reduce workflow sprawl, not preserve it forever.

### 2. Make central credentials ready

Move or copy any secret required by a workflow that will execute centrally into the Actions secrets for `HereLiesAz/workflows`.

Do not remove the target copy yet. Secret removal happens only after the migrated workflow has been tested successfully.

`GH_TOKEN` must include the target repository in its selected repository access before the real sync. If the target is outside its scope, the controller will be unable to replace workflows, set the Worker variable, publish commit statuses, or perform privileged target operations.

### 3. Run a dry sync

Open **Actions → Sync repository workflows → Run workflow** in `HereLiesAz/workflows`.

Set:

```text
repository: HereLiesAz/<repo>
dry_run: true
```

The dry run changes nothing. Read the `sync-result.json` summary and review every workflow classification.

For each workflow, explicitly decide whether the result is correct:

- `catalog`: safe to centralize and reuse.
- `library`: correct if it is a reusable `workflow_call` helper.
- `local`: verify the reported blocker is legitimate and that local execution is desired.
- disabled/obsolete: add it to repository policy instead of preserving it.

Do not run the destructive sync until every workflow has an intentional destination.

### 4. Add repository policy when cleanup is needed

Optional per-repository policy lives at:

```text
registry/<repository-id>/policy.json
```

`disabled_workflows` can list obsolete target workflow paths that should be removed instead of migrated. The synchronizer applies this policy before catalog binding and prunes their registry entries/source snapshots afterward.

Example:

```json
{
  "disabled_workflows": [
    ".github/workflows/obsolete-template.yml"
  ]
}
```

Use this for genuinely unwanted automation, not for workflows that merely need to remain local.

### 5. Run the real sync

Run **Sync repository workflows** again with:

```text
repository: HereLiesAz/<repo>
dry_run: false
```

The synchronizer will:

1. enforce immutable `HereLiesAz` ownership;
2. apply any disabled-workflow policy;
3. set/update `WORKFLOWS_GATEWAY_URL` in the target repository;
4. store each original source under `registry/<repository-id>/`;
5. bind curated workflows to their canonical catalog implementations;
6. deduplicate other centrally safe workflows by implementation hash;
7. keep `workflow_call` helpers as libraries;
8. leave or restore repository-bound workflows locally;
9. replace centrally executed workflows with secretless OIDC proxies;
10. update `registry/<repository-id>/manifest.json`;
11. garbage-collect obsolete legacy `absorbed-<repo-id>-*.yml` executors.

## What a healthy converted repository looks like

After conversion, verify all of these conditions:

### Target repository

- Centrally executed workflows are small proxy files beginning with:

  ```text
  # centralized-by: HereLiesAz/workflows
  ```

- Proxy permissions are limited to `contents: read` and `id-token: write` unless there is an explicitly reviewed reason otherwise.
- Proxies contain no central service secrets.
- `WORKFLOWS_GATEWAY_URL` points to `https://workflows.hereliesaz.workers.dev`.
- Repository-bound workflows remain complete local workflows.
- `workflow_call` helper/library workflows remain available locally when callers need them.
- Obsolete workflows are gone.

### Central repository

- `registry/<repository-id>/manifest.json` contains an entry for each managed workflow.
- Original workflow sources are retained under `registry/<repository-id>/` for validation, restoration, and source-hash checks.
- Shared implementations live in the catalog, not in per-repository `absorbed-*` workflow files.
- No new legacy `absorbed-<repository-id>-*.yml` files remain after a successful sync.

## Runtime verification

Do not call a repository converted until at least one centralized workflow has been exercised end to end.

For a low-risk test, prefer a manual/read-only workflow such as Context Backup or another workflow that does not mutate product code. When no manual trigger is available, use a deliberately isolated event and clean it up afterward.

Verify this entire chain:

```text
target trigger
→ proxy succeeds
→ GitHub OIDC token issued
→ Cloudflare Worker accepts request
→ central gateway dispatches the expected catalog workflow
→ immutable target validation succeeds
→ target commit status becomes pending
→ shared workflow performs the intended target operation
→ target commit status becomes success/failure appropriately
```

A successful central run reports back through **commit statuses**, not GitHub Check Runs. The status context is the original workflow path, which keeps it ASCII, stable, and unique.

For Jules/Glee specifically, also verify that their behavior matches the intended mutation boundary. Glee is repoless and receives only PR metadata plus the unified diff; it must post one `<!-- glee-audit -->` audit comment and must not create branches, commits, or PRs.

## Removing target secrets after migration

Only after runtime verification succeeds should duplicated target Actions secrets be removed.

Before deleting a target secret, search all workflows that remain `local` and all local scripts/actions to confirm they no longer reference it. A repository can be partly centralized, so a secret may still legitimately be required by a local workflow.

Repository variables should receive the same review. `WORKFLOWS_GATEWAY_URL` is intentionally retained because proxies require it.

## Re-running sync later

The synchronizer is intended to be re-run as workflows evolve.

If a target file is already a proxy, the controller recovers the original source from the registry rather than treating proxy code as the workflow implementation. It can then reclassify the original workflow safely.

If a previously central workflow becomes repository-bound, the controller records it as `local` and restores its original source to the target repository. If a reusable helper is encountered, it is restored/kept as `library`.

If the implementation of a safe non-curated workflow changes, its content hash changes and it can bind to a different shared catalog entry. Identical implementations across repositories converge on the same content-addressed catalog workflow.

## Rollback

The registry preserves the original source for each managed workflow. If a central binding must be undone, restore the relevant `registry/<repository-id>/<slug>.source.yml` content to the original target path, remove the proxy, and update/re-run synchronization so the manifest reflects the intended local state.

Do not delete registry source snapshots merely because a workflow was centralized successfully; they are part of the controller's source-hash validation and recovery path.

## Checklist we will use for each repository

For every repository we convert together, use this order:

1. inventory workflows, secrets, variables, local actions, and scripts;
2. identify obsolete/duplicate workflows;
3. decide which existing workflows should map to a curated shared implementation;
4. inspect workflows likely to remain local and document why;
5. ensure central `GH_TOKEN` can access the repository;
6. ensure required central secrets exist;
7. run dry sync;
8. review every classification and blockers;
9. add cleanup policy if needed;
10. run real sync;
11. inspect target proxies/local workflows and central manifest/catalog bindings;
12. run one safe end-to-end smoke test;
13. verify commit status and intended side effects;
14. remove duplicated target secrets only after successful verification;
15. perform a final workflow/branch/PR cleanup caused by migration testing.

A repository is finished only when its workflow set is simpler than before, shared implementations are genuinely reused, local workflows are local for a documented reason, and the runtime path has been proven.
# Repository onboarding

This is the conversion contract for binding a `HereLiesAz/*` repository to the centralized workflow controller.

## Steady-state architecture

A centrally managed repository keeps one **tracker** per centralized workflow, at the workflow's original path, so its `.github/workflows` still lists everything it runs. A tracker keeps the original name and triggers and has one job per central job, with the same names and dependencies. Each job follows its central counterpart, printing steps as they finish and then the job's log, and ends with its result. The repository's Actions tab reads as if the workflow ran there. Trackers never build or dispatch anything. If no central run starts for an event within 20 minutes, the tracker ends neutral.

```text
repository event
  → GitHub repository webhook
  → workflows.hereliesaz.workers.dev/webhook
  → HMAC + immutable owner/repository validation
  → HereLiesAz/workflows/gateway.yml
  → registry trigger matching
  → centralized workflow executor
  → target operation + commit status
```

The Worker already has `DISPATCH_TOKEN`. The webhook signing key is deterministically derived inside the Worker from that secret with a separate HMAC context; the raw token is never used as the webhook secret and no additional shared secret has to be copied into target repositories.

The legacy OIDC `/dispatch` endpoint exists only to drain old proxies during migration.

## What is stored centrally

For every managed workflow, `registry/<repository-id>/` retains the original source and `manifest.json` records its status, source hash, semantic purpose and central executor binding.

The original source is important even after the target workflow file is gone: its `on:` section remains the trigger contract. The central dispatcher evaluates the delivered webhook against that contract, including action types, branch/tag filters and path/path-ignore filters.

Project-local scripts and composite actions remain in the project. A central executor checks out the target repository at the triggering SHA before using them.

## Classification

- **active / curated** — bound to a generalized central implementation.
- **active / repository** — centrally executed but still has repository-specific behavior that has not yet converged on a generalized implementation.
- **library** — pure `workflow_call` source retained while centralized callers still need expansion.
- **local / ci** — target CI (`ci: true`). Runs in the target repository by design and reports progress centrally; never centralized. See [CI runs in its own repository](../README.md#ci-runs-in-its-own-repository).
- **local** — not yet safe to centralize. The blocker is explicit and must be fixed; this is a migration state, not the desired endpoint.
- **blocked/disabled** — intentionally prevented from executing.

A workflow that combines `workflow_call` with real triggers such as `push` is not automatically a library. Its automatic behavior is centralized; only pure `workflow_call` helpers receive library treatment.

## Safe migration order

1. Inventory the target's workflows, local actions/scripts, variables and referenced secrets.
2. Run **Sync repository workflows** with `dry_run: true`.
3. Fix any false/local blockers rather than creating new target-only automation.
4. Ensure the central controller already has the required secret names. New secrets must be explicitly documented by name and purpose.
5. Run the real sync.
6. The controller first asks the Worker to register/update the target repository webhook. If that fails, migration stops before target workflow removal.
7. Original workflow sources are stored in the central registry and implementations are compiled/bound centrally.
8. Controller-generated proxy files are replaced by trackers in one target commit (`[skip ci]`), and a tracker is restored for any active binding whose file is missing. Any truly local blocker is preserved as its original workflow, never as a proxy.
9. Exercise a low-risk repository event and verify central dispatch plus the target commit status.
10. If the repository publishes releases, move shared version/tag/release semantics into the central release family/actions and verify the first grouped release.
11. Only then remove duplicated target secrets that no remaining local workflow uses.

## Release migration

For repositories using four-part versions, onboarding includes release-history normalization.

The target keeps its exact `MAJOR.MINOR.PATCH.BUILD` Git tags. The centralized publisher groups
artifacts under `MAJOR.MINOR.PATCH` GitHub Releases and can migrate legacy four-part Release objects
without deleting their tags. Before enabling migration, confirm artifact filenames are unique per
build or allow the centralized action to inject the exact version.

Do not delete old exact-build tags as a cleanup step. They are the durable build identity.

See [Central release and version policy](RELEASE_VERSIONING.md).

## Repository webhook registration

`sync-repository.yml` and each `sync-all-repositories.yml` matrix job request an Actions OIDC token belonging to **HereLiesAz/workflows** and call:

```text
POST https://workflows.hereliesaz.workers.dev/register
```

The Worker accepts registration only from the central controller, validates the immutable target repository ID/owner using GitHub's API, and creates or updates one active `web` hook for all repository events.

GitHub signs deliveries to `/webhook`. The Worker rejects a delivery before routing unless the signature validates.

## Worker event filter

Every event the Worker forwards starts one `gateway.yml` run, so the Worker first drops events no
registered workflow could consume. `worker/src/event-consumers.js` maps each registered repository ID
to the webhook event names its workflows are triggered by, and is generated by
`scripts/generate_event_consumers.py` with the same rules the gateway routes by:

- only manifest entries with status `active` count (`local`, `library`, `obsolete` and blocked entries are never routed);
- the event names are the keys of the registered source's original `on:`;
- a `pull_request_target` trigger is satisfied by the `pull_request` webhook (GitHub delivers no `pull_request_target` webhook);
- `schedule` and `workflow_call` are not webhooks and are ignored; `workflow_dispatch` is a webhook (a manual run in the target) and is kept;
- `push` is always forwarded for a registered repository, because a push that changes its workflow setup requests a re-sync.

Branch, tag, path and action filters are **not** applied in the Worker; the gateway still makes the exact
routing decision for every forwarded event. Repositories without a registry manifest are dropped. `ping`
is still answered before the filter.

The map stays current on its own: `sync_repository.py` rewrites the synced repository's row after every
real sync, and `sync-all-repositories.yml` regenerates the whole map in its atomic fold commit.
`validate-controller.yml` runs `scripts/test_event_consumers.py`, which fails when the committed map is
stale or when the real routing function (`dispatch_request._event_trigger`) would accept an event the map
drops, and redeploys the Worker when the map changes. After hand-editing a manifest, run
`python scripts/generate_event_consumers.py` and commit the result;
`python scripts/generate_event_consumers.py --list` prints every forwarded (repository, event) pair.

## Trigger behavior

Webhook events are matched centrally against each active registered source.

Supported matching includes:

- `push` branch/tag filters;
- `pull_request` and `pull_request_target` action/branch/path filters;
- issue/comment/review and other repository webhook event action types;
- `repository_dispatch` event types;
- original path and path-ignore rules.

The dispatcher fetches pull-request changed-file lists from GitHub when path filters require them.

Manual `workflow_dispatch` and cron schedules are controller concerns: trackers never dispatch, so they are invoked/scheduled centrally. A tracker's own manual run only mirrors.

## Concurrency

Centralization is **not** global serialization.

- Different repositories/workflows may run concurrently.
- Manual repository sync locks are per target repository, not account-wide.
- `sync-all` uses a matrix and intentionally runs multiple repositories in parallel.
- Only workflows mutating the same external resource should serialize, for example one app's Google Play edit.
- Superseded validation runs on the same controller ref are cancelled; validation on different refs remains concurrent.

## What a healthy converted repository looks like

### Target repository

- no file beginning with `# centralized-by: HereLiesAz/workflows`;
- no `WORKFLOWS_GATEWAY_URL` variable required by the controller;
- one active repository webhook pointing to the central Worker;
- local workflows only where the manifest records a real migration blocker, plus its own CI (`ci: true`), with any `required_secrets` set in the target;
- no copied central service credentials solely for centrally executed workflows.

### Central repository

- original source snapshots and a manifest exist for the target repository ID;
- every active entry resolves to a central executor;
- repository-specific executors exist only when behavior is genuinely unique and are expected to converge toward generalized workflows;
- dispatch results are reported back to the triggering target SHA;
- release-capable bindings use centralized release/version primitives instead of project-local copies of the same policy.

## Rollback

Registry source snapshots are the recovery source. If central execution for a workflow must be rolled back, restore the registered source to its original target path, replacing the tracker, and mark the manifest entry local. Do not recreate a dispatching proxy.

Webhook registration itself is safe to leave in place during rollback; events no active workflow consumes are dropped by the Worker, and unmatched events are ignored by the central dispatcher.

## Completion standard

A repository is finished when intended automation still exists, every centralized workflow has a tracker and no dispatching proxy remains, remaining local workflows have explicit unresolved blockers, central event routing has been exercised, and duplicated secrets have been removed only after successful runtime verification.

## Syncing from the target repository

A registered repository re-syncs itself whenever a push to its default branch changes
`.github/workflows/**` or `.github/workflow-request.yml`. The gateway sees the push
through the repository webhook and starts **Sync repository workflows** for that
repository alone.

So anyone with write access to the target repository alone, including an LLM
session granted only that repository, can add, change or remove centralized
workflows: commit the workflow source (or the request menu change) to the default
branch and the controller registers and binds it, then replaces the file with its
tracker. The synchronizer's own commits carry `[skip ci]`, so they never trigger
another sync.

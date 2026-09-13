# workflows

Central workflow controller for repositories owned by `HereLiesAz`.

Target repositories are migrated to secretless OIDC proxy workflows. The Cloudflare Worker verifies GitHub identity, dispatches the central gateway, and the central executor re-validates immutable repository ownership before using privileged credentials.

Each absorbed workflow remains a separate workflow centrally and publishes its own Check Run back to the originating commit/PR.

## Bootstrap

1. Deploy `worker/` to Cloudflare and configure its `DISPATCH_TOKEN`.
2. Add the central repository secret `GH_TOKEN` and any workflow-specific secrets here.
3. Set the central repository variable `WORKER_URL` to the Worker URL.
4. Run **Sync repository workflows** and enter a repository such as `HereLiesAz/haive`.

The synchronizer stores originals under `registry/<repository-id>/`, creates central executors under `.github/workflows/`, and replaces supported target workflows with secretless proxies. Unsupported workflows are left untouched and recorded as blocked rather than silently altered.

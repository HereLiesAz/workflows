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


## Secret locations

### Cloudflare Worker

The Cloudflare Worker should contain only:

* `DISPATCH_TOKEN`

`DISPATCH_TOKEN` should be a fine-grained GitHub token restricted to `HereLiesAz/workflows` with only the permissions required to dispatch GitHub Actions workflows.

Do not store workflow credentials, signing material, API keys, deployment credentials, or `GH_TOKEN` in Cloudflare.

### `HereLiesAz/workflows`

The following repository secrets belong in the central `HereLiesAz/workflows` repository:

* `GH_TOKEN`
* `JULES_API_KEY`
* `KEYSTORE_PASSWORD`
* `KEY_ALIAS`
* `KEY_PASSWORD`
* `KEYSTORE_OWNER`
* `KEYSTORE_SHA1`
* `KEYSTORE_SHA256`
* `KEYSTORE_PRIVATE`
* `KEYSTORE_PUBLIC`
* `KEYSTORE_CHAIN`
* `KEYSTORE_RSA`
* `KEYSTORE_RAW`
* `PLAY_SERVICE_ACCOUNT_JSON`
* `SNYK_TOKEN`
* `FTP_SERVER`
* `FTP_USERNAME`
* `FTP_PASSWORD`

`GH_TOKEN` is the privileged GitHub credential used by the central controller and absorbed workflows to operate on explicitly authorized `HereLiesAz` repositories. Its repository access and permissions should remain as narrow as practical.

### Keystore rule

`KEYSTORE_RAW` is provided for **verification purposes only**.

It must never be used directly as the signing keystore.

Signing workflows must reconstruct the keystore from the other keystore-related repository secrets, verify the reconstructed keystore using the supplied fingerprints and verification material, and use only the reconstructed keystore for signing.

Target repositories should not retain duplicated Actions secrets after their workflows have been successfully centralized.

# Generalized workflow policy

New GitHub Actions implementations for repositories owned by HereLiesAz are centralized in this repository.

## Scope

Only **public** repositories owned by HereLiesAz are registered, synced, and served by the gateway.
`sync-all-repositories.yml` excludes private repositories from discovery, and `sync_repository.py`
refuses to sync one directly even when targeted by hand. A private repository stays entirely off the
shared catalog; make it public first if it needs centralized workflows.

## Admission rules

A new target-repository workflow file is rejected by repository synchronization unless that workflow path is already registered. New capabilities must be submitted here first.

A new workflow added to `.github/workflows/` in this repository must:

1. declare `# workflow-policy: generalized-v1`;
2. declare a generic `# workflow-purpose:`;
3. expose a required `target_repository` workflow-dispatch input;
4. avoid hard-coded target repository names and HereLiesAz package/application IDs;
5. parameterize repository-specific paths, branches, package/application identifiers, release names, and artifacts;
6. reuse names from `policy/workflow-policy.json` whenever an existing secret satisfies the requirement;
7. declare every referenced secret as `# required-secret: NAME | purpose`;
8. add a `policy_secret_preflight` job that reports a missing required secret by **name and purpose** before the actual work begins.

Existing workflow paths present when the policy was introduced are listed in `grandfathered_workflows`. They continue to work unchanged; the policy is not a cleanup excuse.

## Submission paths

- Use the **Generalized workflow submission** issue form for a new capability request.
- Use `templates/generalized-workflow.yml` when implementing it.
- Use `templates/repository-workflow-request.yml` in repository templates and new repositories to show the available menu without copying executable workflow implementations.

## Secret catalog

`policy/workflow-policy.json#secret_catalog` contains secret **names and purposes only**. It never contains secret values.

When no existing secret provides the required authority, add the new name and its purpose to that catalog and make the workflow fail explicitly if the secret is absent.


## Release and version policy

Release workflows are subject to the same centralization rule as build/test workflows.

When a project uses `MAJOR.MINOR.PATCH.BUILD` versions:

- use `.github/actions/four-part-version` for BUILD derivation;
- use `.github/actions/patch-grouped-release` for Git tags and GitHub Release publication;
- keep exact four-part tags immutable;
- group build artifacts under the three-part patch Release (`MAJOR.MINOR.PATCH`);
- keep the full four-part version in asset names;
- never use clobber semantics to replace different bytes under an existing grouped asset name; and
- preserve exact-build tags when legacy one-build-per-Release objects are migrated.

Generalized Android, multi-platform, and artifact release families apply this automatically when the
resolved version is four-part. Non-four-part profiles retain their existing release behavior.

A target workflow may contain artifact-building logic that is genuinely target-specific, but it must
not duplicate central tag/grouping/version policy merely for convenience. See
[`RELEASE_VERSIONING.md`](RELEASE_VERSIONING.md).

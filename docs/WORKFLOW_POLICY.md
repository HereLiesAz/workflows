# Generalized workflow policy

New GitHub Actions implementations for repositories owned by HereLiesAz are centralized in this repository.

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

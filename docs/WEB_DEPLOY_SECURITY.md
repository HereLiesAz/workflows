# Web deploy: exposure and mitigations

`web-deploy.yml` builds a commit of a (possibly private) HereLiesAz repository inside
`HereLiesAz/workflows`, which is a **public** repository. GitHub Actions runs of a public repository
are world-readable.

## Mitigated in code

- The run name is `Web Deploy · repository <numeric id>`. Dispatch inputs are only the numeric
  repository id and the commit SHA; the repository name and the Pages project name are not inputs.
- Each job resolves the repository name from the id, then registers the name and the SHA with
  `::add-mask::` before any other step. The inputs are read from the event payload, and the checkout
  is a plain `git fetch` rather than `actions/checkout`, so no step header (`env:`/`with:`) prints them.
- The Pages project name is derived in the workflow from the repository id and name (same algorithm
  as `pagesProjectName()` in `worker/src/web-deploy.js`), so a dispatcher cannot overwrite another
  project's site.
- The no-build fallback publishes an allow-list of static types only (html, css, js, images, fonts,
  json, txt, webmanifest, ico, svg), never dotfiles, `node_modules`, or names that look like
  secrets (`secret`, `credential`, `local.properties`, `google-services.json`, keys, ...).
- `_worker.js`, `_routes.json` and `functions/` are removed from every published output, so a project
  cannot deploy server-side code onto the central Cloudflare account.
- Wrangler is pinned to an exact version and run from an empty directory.
- The dead check-run / failure-issue steps (which referenced inputs this workflow never had) are
  removed, so no log tail is ever copied into an issue.

## Remaining exposure (needs an infrastructure decision)

- The **build job's own output** (`npm ci` / `npm run build` logs, stack traces, file paths,
  source snippets, anything the project's scripts print) is still written to a public Actions run.
  Masking only covers the repository name and SHA, not what project code chooses to print.
  The real fix is to run private builds in a **private** repository (or on a private runner), not here.
- A project's built site is public on `*.pages.dev` by design.
- Run existence, timing and the numeric repository id remain visible.

Until builds move to a private repository, treat any private project deployed through this route as
having public build logs.

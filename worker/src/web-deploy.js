// Web deploy: builds one pushed commit of a repository and publishes only its build output.
//
// IDEaz (HereLiesAz/IDEaz) calls this after pushing a project to its own, private, repository.
// None of the other routes fit that caller: /register and /remote-run/start accept only this
// repository's Actions OIDC, /webhook needs a registered hook and the registry excludes private
// repositories, and the legacy /dispatch needs a workflow file in the target. So the project
// carries no workflow at all; the Worker dispatches the central web-deploy.yml, which builds the
// commit without secrets, publishes the output directory to Cloudflare Pages with the central
// credentials, and reports back as a commit status the app polls.
//
// The caller authenticates with its own GitHub token, which is used for exactly one read: the
// repository as that token sees it, which must grant push. The token is never stored or forwarded.

const OWNER_LOGIN = "HereLiesAz";
const OWNER_ID = "103241502";
const CENTRAL_REPOSITORY = "HereLiesAz/workflows";
const MAX_BODY_BYTES = 16 * 1024;
const MAX_PAGES_PROJECT_CHARS = 58;

export const WEB_DEPLOY_WORKFLOW = "web-deploy.yml";
export const WEB_DEPLOY_STATUS_CONTEXT = "ideaz/web-deploy";

/**
 * The Cloudflare Pages project for a repository: lowercase letters, digits and dashes, at most
 * 58 characters. The repository ID keeps two names that slug alike ("My.App", "my-app") apart,
 * and keeps the project stable across a rename.
 */
export function pagesProjectName(repositoryName, repositoryId) {
  const id = String(repositoryId);
  if (!/^\d+$/.test(id)) throw new Error("repository ID must be numeric");
  const suffix = `-${Number(id).toString(36)}`;
  const slug = String(repositoryName || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  const head = `ideaz-${slug}`.slice(0, MAX_PAGES_PROJECT_CHARS - suffix.length).replace(/-+$/g, "");
  return `${head}${suffix}`;
}

export function pagesSiteUrl(project) {
  return `https://${project}.pages.dev`;
}

/**
 * POST /web-deploy {repository: "HereLiesAz/name", sha: "<40 hex>"}
 * Authorization: Bearer <the caller's GitHub token>
 *
 * appApi(path, method, body, allowEmpty) calls GitHub as this Worker's App and throws on failure.
 * callerApi(token, path) calls GitHub with the caller's token and returns {status, body}.
 */
export async function receiveWebDeploy(request, { appApi, callerApi }) {
  const bearer = request.headers.get("Authorization") || "";
  const match = bearer.match(/^Bearer\s+(\S+)$/i);
  if (!match) return json({ ok: false, error: "Missing GitHub token" }, 401);

  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
    return json({ ok: false, error: "Request payload is too large" }, 413);
  }
  let body;
  try {
    body = JSON.parse(raw);
  } catch {
    return json({ ok: false, error: "Request body is not valid JSON" }, 400);
  }
  const repository = String(body?.repository || "");
  const sha = String(body?.sha || "").toLowerCase();
  if (!/^[A-Za-z0-9-]{1,39}\/[A-Za-z0-9_.-]{1,100}$/.test(repository)) {
    return json({ ok: false, error: "repository is invalid" }, 400);
  }
  if (!/^[a-f0-9]{40}$/.test(sha)) return json({ ok: false, error: "sha is invalid" }, 400);

  // The caller's own view of the repository: proves the token may push to it.
  const seen = await callerApi(match[1], `/repos/${repository}`);
  if (seen.status === 401) return json({ ok: false, error: "GitHub rejected the token" }, 401);
  if (seen.status !== 200) return json({ ok: false, error: "The token cannot see this repository" }, 403);
  if (seen.body?.permissions?.push !== true) {
    return json({ ok: false, error: "The token cannot push to this repository" }, 403);
  }
  if (!isOwned(seen.body)) {
    return json({
      ok: false,
      error: `Central web deploy serves only repositories owned by ${OWNER_LOGIN}`,
    }, 403);
  }

  // The App's view: same repository, and the App can reach it to build it.
  const repo = await appApi(`/repos/${repository}`);
  if (!isOwned(repo) || String(repo.id) !== String(seen.body.id)) {
    return json({ ok: false, error: "Repository identity mismatch" }, 409);
  }
  // A commit that was never pushed has nothing to build.
  await appApi(`/repos/${repository}/commits/${sha}`);

  const project = pagesProjectName(repo.name, repo.id);
  await appApi(
    `/repos/${CENTRAL_REPOSITORY}/actions/workflows/${WEB_DEPLOY_WORKFLOW}/dispatches`,
    "POST",
    {
      ref: "main",
      inputs: {
        target_repository: repo.full_name,
        target_repository_id: String(repo.id),
        target_sha: sha,
        pages_project: project,
      },
    },
    true,
  );

  return json({
    ok: true,
    repository: repo.full_name,
    sha,
    status_context: WEB_DEPLOY_STATUS_CONTEXT,
    site_url: pagesSiteUrl(project),
  }, 202);
}

function isOwned(repo) {
  return String(repo?.owner?.id) === OWNER_ID &&
    String(repo?.owner?.login || "").toLowerCase() === OWNER_LOGIN.toLowerCase();
}

function json(value, status) {
  return new Response(JSON.stringify(value, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

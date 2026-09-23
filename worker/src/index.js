import { receiveCrashReport } from "./crash-report.js";

const GITHUB_ISSUER = "https://token.actions.githubusercontent.com";
const GITHUB_JWKS = "https://token.actions.githubusercontent.com/.well-known/jwks";
const EXPECTED_AUDIENCE = "hereliesaz-workflows";
const OWNER_LOGIN = "HereLiesAz";
const OWNER_ID = "103241502";
const CENTRAL_REPOSITORY = "HereLiesAz/workflows";
const GATEWAY_WORKFLOW = "gateway.yml";
const API_VERSION = "2026-03-10";
const MAX_REQUEST_JSON_BYTES = 5 * 1024 * 1024;
const MAX_WORKFLOW_DISPATCH_INPUT_CHARS = 60000;
const IGNORED_WEBHOOK_EVENTS = new Set(["check_run", "check_suite", "workflow_job", "status"]);

let jwksCache;
let jwksCacheExpiresAt = 0;
let githubInstallationTokenCache = "";
let githubInstallationTokenExpiresAt = 0;
// GitHub API traffic uses short-lived App installation tokens, never DISPATCH_TOKEN.

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "HereLiesAz/workflows gateway", mode: "webhook-central" });
    }
    if (request.method === "GET" && url.pathname === "/repositories") {
      return await scrapePublicRepositories(url);
    }

    try {
      if (request.method === "POST" && url.pathname === "/register") {
        return await registerRepositoryWebhook(request, env, url);
      }
      if (request.method === "POST" && url.pathname === "/webhook") {
        return await receiveRepositoryWebhook(request, env);
      }
      const crashRoute = url.pathname.match(/^\/crash-report\/([A-Za-z0-9_.-]{1,100})$/);
      if (request.method === "POST" && crashRoute) {
        return await receiveCrashReport(request, crashRoute[1], (path, method, body) =>
          githubApi(env, path, method, body));
      }
      if (request.method === "POST" && url.pathname === "/dispatch") {
        return await receiveLegacyOidcDispatch(request, env);
      }
      return new Response("Not found", { status: 404 });
    } catch (error) {
      if (error instanceof HttpError) {
        return json({ ok: false, error: error.message }, error.status);
      }
      console.error(error);
      return json({ ok: false, error: "Internal gateway error" }, 500);
    }
  },
};

async function scrapePublicRepositories(url) {
  const repositories = [];
  const seen = new Set();
  const stop = String(url.searchParams.get("stop") || "").trim();
  const stopFullName = stop && stop.includes("/") ? stop : (stop ? `${OWNER_LOGIN}/${stop}` : "");
  let stopFound = false;
  let pageUrl = `https://github.com/${OWNER_LOGIN}?tab=repositories&q=&type=public&language=&sort=`;
  let pagesScanned = 0;

  while (pageUrl && pagesScanned < 20 && !stopFound) {
    pagesScanned += 1;
    const response = await fetch(pageUrl, {
      headers: {
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": "HereLiesAz-workflows-public-repository-discovery",
      },
      cf: { cacheTtl: 300, cacheEverything: true },
    });
    if (!response.ok) {
      throw new HttpError(502, `GitHub public repository page failed (${response.status})`);
    }

    let foundOnPage = 0;
    let nextHref = "";
    const currentPage = pagesScanned;
    const rewriter = new HTMLRewriter().on("a[href]", {
      element(element) {
        const href = element.getAttribute("href") || "";

        // Preserve GitHub's own pagination URL instead of reconstructing it.
        if (href.includes("tab=repositories") && href.includes("type=public") && /[?&]page=\d+/.test(href)) {
          try {
            const candidate = new URL(href, "https://github.com");
            const candidatePage = Number(candidate.searchParams.get("page") || "0");
            if (candidatePage === currentPage + 1) nextHref = candidate.toString();
          } catch {}
        }

        if (stopFound) return;
        const match = href.match(/^\/HereLiesAz\/([A-Za-z0-9_.-]+)$/i);
        if (!match) return;
        const name = match[1];
        if (name.toLowerCase() === "workflows") return;
        const fullName = `${OWNER_LOGIN}/${name}`;

        if (stopFullName && fullName.toLowerCase() === stopFullName.toLowerCase()) {
          stopFound = true;
          return;
        }
        if (!seen.has(fullName)) {
          seen.add(fullName);
          repositories.push(fullName);
          foundOnPage += 1;
        }
      },
    });
    await rewriter.transform(response).text();

    if (stopFound || foundOnPage === 0) break;
    pageUrl = nextHref;
  }

  if (stopFullName && !stopFound) {
    throw new HttpError(409, `Expected repository cursor not found: ${stopFullName}`);
  }

  return json({
    ok: true,
    owner: OWNER_LOGIN,
    repositories,
    count: repositories.length,
    stop_repository: stopFullName || null,
    stop_found: stopFound,
    pages_scanned: pagesScanned,
    source: "github-public-html",
  });
}

async function registerRepositoryWebhook(request, env, url) {
  requireDispatchToken(env);

  const bearer = request.headers.get("Authorization") || "";
  const match = bearer.match(/^Bearer\s+(.+)$/i);
  if (!match) throw new HttpError(401, "Missing central Actions OIDC bearer token");

  const claims = await verifyGitHubOidc(match[1]);
  if (String(claims.repository || "").toLowerCase() !== CENTRAL_REPOSITORY.toLowerCase()) {
    throw new HttpError(403, "Only HereLiesAz/workflows may register repository webhooks");
  }
  if (String(claims.repository_owner_id || "") !== OWNER_ID) {
    throw new HttpError(403, "Central workflow owner mismatch");
  }

  const body = await readJsonBody(request);
  const repository = String(body.repository || "");
  const repositoryId = String(body.repository_id || "");
  if (!/^HereLiesAz\/[A-Za-z0-9_.-]+$/.test(repository)) {
    throw new HttpError(400, "repository is required");
  }

  const repo = await githubApi(env, `/repos/${repository}`);
  if (repositoryId && String(repo.id) !== repositoryId) throw new HttpError(409, "Repository ID mismatch");
  if (String(repo.owner?.id) !== OWNER_ID ||
      String(repo.owner?.login || "").toLowerCase() !== OWNER_LOGIN.toLowerCase()) {
    throw new HttpError(403, "Repository is not owned by HereLiesAz");
  }

  const webhookUrl = `${url.origin}/webhook`;
  const secret = await derivedWebhookSecret(env);
  const hooks = await githubApi(env, `/repos/${repository}/hooks?per_page=100`);
  const existing = Array.isArray(hooks)
    ? hooks.find((hook) => String(hook?.config?.url || "") === webhookUrl)
    : undefined;

  const payload = {
    name: "web",
    active: true,
    events: ["*"],
    config: {
      url: webhookUrl,
      content_type: "json",
      insecure_ssl: "0",
      secret,
    },
  };

  let hook;
  if (existing?.id) {
    hook = await githubApi(env, `/repos/${repository}/hooks/${existing.id}`, "PATCH", payload);
  } else {
    hook = await githubApi(env, `/repos/${repository}/hooks`, "POST", payload);
  }

  return json({
    ok: true,
    repository,
    repository_id: String(repo.id),
    hook_id: hook?.id,
    webhook_url: webhookUrl,
    events: ["*"],
  }, existing ? 200 : 201);
}

async function receiveRepositoryWebhook(request, env) {
  requireDispatchToken(env);
  const rawBody = await readRawBody(request);
  const signature = request.headers.get("X-Hub-Signature-256") || "";
  if (!signature.startsWith("sha256=")) throw new HttpError(401, "Missing GitHub webhook signature");

  const valid = await verifyWebhookSignature(env, rawBody, signature.slice("sha256=".length));
  if (!valid) throw new HttpError(401, "Invalid GitHub webhook signature");

  const eventName = request.headers.get("X-GitHub-Event") || "";
  const delivery = request.headers.get("X-GitHub-Delivery") || crypto.randomUUID();
  if (!eventName) throw new HttpError(400, "Missing X-GitHub-Event");

  let event;
  try {
    event = JSON.parse(rawBody);
  } catch {
    throw new HttpError(400, "Webhook body is not valid JSON");
  }

  if (eventName === "ping") {
    return json({ ok: true, pong: true, zen: event.zen || "" });
  }

  // These GitHub lifecycle events currently have no registered workflow
  // consumers. Dropping them here prevents check/job activity from recursively
  // creating gateway runs that can never dispatch anything.
  if (IGNORED_WEBHOOK_EVENTS.has(eventName)) {
    return json({ ok: true, ignored: true, event_name: eventName, reason: "No registered workflow consumes this event" }, 202);
  }

  const repository = event.repository;
  if (!repository?.full_name || repository?.id === undefined) {
    return json({ ok: true, ignored: true, reason: "Webhook event has no repository" }, 202);
  }
  if (String(repository.owner?.id) !== OWNER_ID ||
      String(repository.owner?.login || "").toLowerCase() !== OWNER_LOGIN.toLowerCase()) {
    throw new HttpError(403, "Webhook repository is not owned by HereLiesAz");
  }

  const context = await normalizeWebhookContext(env, eventName, event);
  const sender = event.sender || {};
  const body = {
    repository: repository.full_name,
    repository_id: String(repository.id),
    repository_owner: repository.owner.login,
    repository_owner_id: String(repository.owner.id),
    sha: context.sha,
    check_sha: context.checkSha,
    ref: context.ref,
    ref_name: context.refName,
    ref_type: context.refType,
    head_ref: context.headRef,
    base_ref: context.baseRef,
    actor: String(sender.login || "github"),
    actor_id: sender.id === undefined ? "" : String(sender.id),
    event_name: eventName,
    event,
    inputs: {},
    vars: {},
    run_id: `webhook-${delivery}`,
    run_number: "",
    run_attempt: "1",
    workflow_ref: "",
    workflow_name: "",
    source_workflow_path: "",
    source_sha256: "",
    webhook_delivery: delivery,
  };

  await dispatchGateway(env, body);
  return json({
    ok: true,
    repository: body.repository,
    event_name: eventName,
    delivery,
  }, 202);
}

async function normalizeWebhookContext(env, eventName, event) {
  const repository = event.repository;
  const defaultBranch = String(repository.default_branch || "main");

  if (eventName === "push") {
    const ref = String(event.ref || "");
    const sha = String(event.after || event.head_commit?.id || event.before || "");
    const zero = /^0{40}$/.test(sha);
    const resolvedSha = zero ? await defaultBranchSha(env, repository.full_name, defaultBranch) : sha;
    const refName = ref.replace(/^refs\/(heads|tags)\//, "");
    const refType = ref.startsWith("refs/tags/") ? "tag" : "branch";
    return {
      sha: resolvedSha,
      checkSha: resolvedSha,
      ref,
      refName,
      refType,
      headRef: "",
      baseRef: "",
    };
  }

  if (event.pull_request) {
    const pr = event.pull_request;
    const sha = String(pr.head?.sha || "");
    const headRef = String(pr.head?.ref || "");
    const baseRef = String(pr.base?.ref || "");
    return {
      sha,
      checkSha: sha,
      ref: headRef ? `refs/heads/${headRef}` : `refs/pull/${pr.number || event.number || ""}/head`,
      refName: headRef,
      refType: "branch",
      headRef,
      baseRef,
    };
  }

  if (eventName === "create" || eventName === "delete") {
    const refType = String(event.ref_type || "branch");
    const refName = String(event.ref || defaultBranch);
    const sha = await defaultBranchSha(env, repository.full_name, defaultBranch);
    return {
      sha,
      checkSha: sha,
      ref: `refs/${refType === "tag" ? "tags" : "heads"}/${refName}`,
      refName,
      refType,
      headRef: "",
      baseRef: "",
    };
  }

  const sha = await defaultBranchSha(env, repository.full_name, defaultBranch);
  return {
    sha,
    checkSha: sha,
    ref: `refs/heads/${defaultBranch}`,
    refName: defaultBranch,
    refType: "branch",
    headRef: "",
    baseRef: "",
  };
}

async function defaultBranchSha(env, repository, branch) {
  const commit = await githubApi(env, `/repos/${repository}/commits/${encodeURIComponent(branch)}`);
  const sha = String(commit?.sha || "");
  if (!sha) throw new HttpError(502, `Could not resolve ${repository}:${branch}`);
  return sha;
}

async function receiveLegacyOidcDispatch(request, env) {
  requireDispatchToken(env);

  const bearer = request.headers.get("Authorization") || "";
  const match = bearer.match(/^Bearer\s+(.+)$/i);
  if (!match) throw new HttpError(401, "Missing OIDC bearer token");

  const claims = await verifyGitHubOidc(match[1]);
  const rawBody = await readRawBody(request);

  let body;
  try {
    body = JSON.parse(rawBody);
  } catch {
    throw new HttpError(400, "Request body is not valid JSON");
  }

  validateLegacyDispatch(body, claims);
  await dispatchGateway(env, body);
  return json({
    ok: true,
    repository: body.repository,
    repository_id: String(body.repository_id),
    source_workflow_path: body.source_workflow_path,
    legacy_proxy: true,
  }, 202);
}

async function dispatchGateway(env, body) {
  const requestB64 = await gzipBase64Utf8(JSON.stringify(body));
  if (requestB64.length > MAX_WORKFLOW_DISPATCH_INPUT_CHARS) {
    throw new HttpError(413, "Compressed dispatch payload is too large for workflow_dispatch");
  }

  const response = await githubApi(
    env,
    `/repos/${CENTRAL_REPOSITORY}/actions/workflows/${GATEWAY_WORKFLOW}/dispatches`,
    "POST",
    {
      ref: "main",
      inputs: {
        repository: body.repository,
        repository_id: String(body.repository_id),
        request_b64: requestB64,
      },
    },
    true,
  );
  return response;
}

function validateLegacyDispatch(body, claims) {
  const required = [
    "repository", "repository_id", "repository_owner", "repository_owner_id",
    "sha", "check_sha", "ref", "actor", "event_name", "run_id",
    "workflow_ref", "workflow_name", "source_workflow_path", "source_sha256",
  ];

  for (const key of required) {
    if (body[key] === undefined || body[key] === null || String(body[key]).length === 0) {
      throw new HttpError(400, `Missing field: ${key}`);
    }
  }

  if (String(claims.repository_owner_id) !== OWNER_ID ||
      String(claims.repository_owner || "").toLowerCase() !== OWNER_LOGIN.toLowerCase()) {
    throw new HttpError(403, "OIDC repository owner is not HereLiesAz");
  }
  if (String(body.repository_owner_id) !== OWNER_ID ||
      String(body.repository_owner).toLowerCase() !== OWNER_LOGIN.toLowerCase()) {
    throw new HttpError(403, "Request repository owner is not HereLiesAz");
  }

  for (const key of ["repository", "repository_id", "sha", "ref", "event_name", "actor"]) {
    exactClaim(body, claims, key);
  }

  const expectedCheckSha = body.event?.pull_request?.head?.sha || body.sha;
  if (String(body.check_sha) !== String(expectedCheckSha)) {
    throw new HttpError(403, "check_sha does not match the GitHub event");
  }

  if (!/^\.github\/workflows\/[^/]+\.ya?ml$/.test(String(body.source_workflow_path))) {
    throw new HttpError(400, "source_workflow_path must name a top-level GitHub workflow file");
  }
  if (!/^[a-f0-9]{64}$/i.test(String(body.source_sha256))) {
    throw new HttpError(400, "source_sha256 is invalid");
  }

  const workflowRef = String(claims.workflow_ref || "");
  const expectedPrefix = `${body.repository}/${body.source_workflow_path}@`;
  if (!workflowRef.startsWith(expectedPrefix)) {
    throw new HttpError(403, "OIDC workflow_ref does not match the claimed source workflow");
  }
}

function exactClaim(body, claims, key) {
  if (claims[key] === undefined || String(body[key]) !== String(claims[key])) {
    throw new HttpError(403, `OIDC ${key} does not match request body`);
  }
}

async function readRawBody(request) {
  const rawBody = await request.text();
  if (new TextEncoder().encode(rawBody).byteLength > MAX_REQUEST_JSON_BYTES) {
    throw new HttpError(413, "Request payload is too large");
  }
  return rawBody;
}

async function readJsonBody(request) {
  const raw = await readRawBody(request);
  try {
    return JSON.parse(raw);
  } catch {
    throw new HttpError(400, "Request body is not valid JSON");
  }
}

function requireDispatchToken(env) {
  if (!env.DISPATCH_TOKEN) {
    throw new HttpError(500, "Worker DISPATCH_TOKEN is not configured");
  }
}

async function githubApi(env, path, method = "GET", body = undefined, allowEmpty = false) {
  const token = await githubInstallationToken(env);
  const response = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      "User-Agent": "HereLiesAz-workflows-cloudflare-gateway",
      "X-GitHub-Api-Version": API_VERSION,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    if (response.status === 401) {
      githubInstallationTokenCache = "";
      githubInstallationTokenExpiresAt = 0;
    }
    throw new HttpError(502, `GitHub API failed (${response.status}): ${detail}`);
  }
  if (response.status === 204 || allowEmpty) return null;
  return response.json();
}

async function githubInstallationToken(env) {
  requireGitHubAppCredentials(env);

  const now = Math.floor(Date.now() / 1000);
  if (githubInstallationTokenCache && now < githubInstallationTokenExpiresAt - 120) {
    return githubInstallationTokenCache;
  }

  const appJwt = await createGitHubAppJwt(env);
  const installationsResponse = await fetch("https://api.github.com/app/installations?per_page=100", {
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": `Bearer ${appJwt}`,
      "User-Agent": "HereLiesAz-workflows-cloudflare-gateway",
      "X-GitHub-Api-Version": API_VERSION,
    },
  });
  if (!installationsResponse.ok) {
    const detail = await installationsResponse.text();
    throw new HttpError(502, `GitHub App installation lookup failed (${installationsResponse.status}): ${detail}`);
  }

  const installations = await installationsResponse.json();
  const installation = Array.isArray(installations)
    ? installations.find((item) =>
        String(item?.account?.id) === OWNER_ID &&
        String(item?.account?.login || "").toLowerCase() === OWNER_LOGIN.toLowerCase())
    : undefined;
  if (!installation?.id) {
    throw new HttpError(502, `GitHub App is not installed on ${OWNER_LOGIN}`);
  }

  const tokenResponse = await fetch(
    `https://api.github.com/app/installations/${installation.id}/access_tokens`,
    {
      method: "POST",
      headers: {
        "Accept": "application/vnd.github+json",
        "Authorization": `Bearer ${appJwt}`,
        "Content-Type": "application/json",
        "User-Agent": "HereLiesAz-workflows-cloudflare-gateway",
        "X-GitHub-Api-Version": API_VERSION,
      },
      body: "{}",
    },
  );
  if (!tokenResponse.ok) {
    const detail = await tokenResponse.text();
    throw new HttpError(502, `GitHub App token creation failed (${tokenResponse.status}): ${detail}`);
  }

  const payload = await tokenResponse.json();
  const token = String(payload?.token || "");
  const expiresAt = Date.parse(String(payload?.expires_at || ""));
  if (!token || !Number.isFinite(expiresAt)) {
    throw new HttpError(502, "GitHub App returned an invalid installation token");
  }

  githubInstallationTokenCache = token;
  githubInstallationTokenExpiresAt = Math.floor(expiresAt / 1000);
  return token;
}

function requireGitHubAppCredentials(env) {
  if (!env.GH_APP_ID) throw new HttpError(500, "Worker GH_APP_ID is not configured");
  if (!env.GH_PRIVATE_KEY) throw new HttpError(500, "Worker GH_PRIVATE_KEY is not configured");
}

async function createGitHubAppJwt(env) {
  const now = Math.floor(Date.now() / 1000);
  const header = base64UrlEncodeUtf8(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const payload = base64UrlEncodeUtf8(JSON.stringify({
    iat: now - 60,
    exp: now + 9 * 60,
    iss: String(env.GH_APP_ID),
  }));
  const signingInput = `${header}.${payload}`;
  const key = await importGitHubPrivateKey(String(env.GH_PRIVATE_KEY));
  const signature = await crypto.subtle.sign(
    { name: "RSASSA-PKCS1-v1_5" },
    key,
    new TextEncoder().encode(signingInput),
  );
  return `${signingInput}.${base64UrlEncodeBytes(new Uint8Array(signature))}`;
}

async function importGitHubPrivateKey(pem) {
  const normalized = pem.replace(/\\n/g, "\n").trim();
  let der;
  if (normalized.includes("-----BEGIN PRIVATE KEY-----")) {
    der = pemBodyToBytes(normalized, "PRIVATE KEY");
  } else if (normalized.includes("-----BEGIN RSA PRIVATE KEY-----")) {
    const pkcs1 = pemBodyToBytes(normalized, "RSA PRIVATE KEY");
    der = wrapPkcs1RsaPrivateKeyAsPkcs8(pkcs1);
  } else {
    throw new HttpError(500, "GH_PRIVATE_KEY must contain a PKCS#8 or RSA private-key PEM");
  }

  try {
    return await crypto.subtle.importKey(
      "pkcs8",
      der,
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
      false,
      ["sign"],
    );
  } catch {
    throw new HttpError(500, "GH_PRIVATE_KEY could not be imported as an RSA private key");
  }
}

function pemBodyToBytes(pem, label) {
  const body = pem
    .replace(`-----BEGIN ${label}-----`, "")
    .replace(`-----END ${label}-----`, "")
    .replace(/\s+/g, "");
  if (!body) throw new HttpError(500, `GH_PRIVATE_KEY ${label} PEM is empty`);
  const binary = atob(body);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function wrapPkcs1RsaPrivateKeyAsPkcs8(pkcs1) {
  // PrivateKeyInfo ::= SEQUENCE {
  //   version INTEGER 0,
  //   privateKeyAlgorithm rsaEncryption,
  //   privateKey OCTET STRING (PKCS#1 RSAPrivateKey)
  // }
  const version = new Uint8Array([0x02, 0x01, 0x00]);
  const algorithm = new Uint8Array([
    0x30, 0x0d,
    0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01,
    0x05, 0x00,
  ]);
  const privateKey = derEncode(0x04, pkcs1);
  return derEncode(0x30, concatBytes(version, algorithm, privateKey));
}

function derEncode(tag, value) {
  const length = value.length;
  let lengthBytes;
  if (length < 0x80) {
    lengthBytes = new Uint8Array([length]);
  } else {
    const parts = [];
    let remaining = length;
    while (remaining > 0) {
      parts.unshift(remaining & 0xff);
      remaining >>>= 8;
    }
    lengthBytes = new Uint8Array([0x80 | parts.length, ...parts]);
  }
  return concatBytes(new Uint8Array([tag]), lengthBytes, value);
}

function concatBytes(...arrays) {
  const length = arrays.reduce((sum, item) => sum + item.length, 0);
  const out = new Uint8Array(length);
  let offset = 0;
  for (const item of arrays) {
    out.set(item, offset);
    offset += item.length;
  }
  return out;
}

function base64UrlEncodeUtf8(value) {
  return base64UrlEncodeBytes(new TextEncoder().encode(value));
}

function base64UrlEncodeBytes(bytes) {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + chunkSize, bytes.length)));
  }
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

async function derivedWebhookSecret(env) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(env.DISPATCH_TOKEN),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode("HereLiesAz/workflows:webhook-signing:v1"),
  );
  return bytesToHex(new Uint8Array(signature));
}

async function verifyWebhookSignature(env, rawBody, suppliedHex) {
  if (!/^[0-9a-f]{64}$/i.test(suppliedHex)) return false;
  const secret = await derivedWebhookSecret(env);
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const supplied = hexToBytes(suppliedHex);
  return crypto.subtle.verify(
    "HMAC",
    key,
    supplied,
    new TextEncoder().encode(rawBody),
  );
}

function bytesToHex(bytes) {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function hexToBytes(hex) {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i += 1) out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return out;
}

async function verifyGitHubOidc(token) {
  const parts = token.split(".");
  if (parts.length !== 3) throw new HttpError(401, "Malformed OIDC token");

  let header;
  let claims;
  try {
    header = JSON.parse(new TextDecoder().decode(base64UrlDecode(parts[0])));
    claims = JSON.parse(new TextDecoder().decode(base64UrlDecode(parts[1])));
  } catch {
    throw new HttpError(401, "Malformed OIDC token payload");
  }

  if (header.alg !== "RS256" || !header.kid) throw new HttpError(401, "Unsupported OIDC signing key");
  if (claims.iss !== GITHUB_ISSUER) throw new HttpError(401, "Unexpected OIDC issuer");

  const audiences = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!audiences.includes(EXPECTED_AUDIENCE)) throw new HttpError(401, "Unexpected OIDC audience");

  const now = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(claims.exp) || claims.exp < now - 30) throw new HttpError(401, "Expired OIDC token");
  if (claims.nbf !== undefined && Number(claims.nbf) > now + 30) throw new HttpError(401, "OIDC token is not valid yet");

  let jwks = await getJwks();
  let jwk = jwks.keys.find((key) => key.kid === header.kid && key.kty === "RSA");
  if (!jwk) {
    jwksCacheExpiresAt = 0;
    jwks = await getJwks();
    jwk = jwks.keys.find((key) => key.kid === header.kid && key.kty === "RSA");
  }
  if (!jwk) throw new HttpError(401, "Unknown GitHub OIDC signing key");

  const key = await crypto.subtle.importKey(
    "jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"],
  );
  const signed = new TextEncoder().encode(`${parts[0]}.${parts[1]}`);
  const signature = base64UrlDecode(parts[2]);
  const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, signature, signed);
  if (!valid) throw new HttpError(401, "Invalid GitHub OIDC signature");
  return claims;
}

async function getJwks() {
  const now = Date.now();
  if (jwksCache && now < jwksCacheExpiresAt) return jwksCache;

  const response = await fetch(GITHUB_JWKS, {
    headers: { "Accept": "application/json" },
    cf: { cacheTtl: 3600, cacheEverything: true },
  });
  if (!response.ok) throw new HttpError(502, "Could not load GitHub OIDC signing keys");
  jwksCache = await response.json();
  jwksCacheExpiresAt = now + 60 * 60 * 1000;
  return jwksCache;
}

function base64UrlDecode(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function gzipBase64Utf8(value) {
  const bytes = new TextEncoder().encode(value);
  const compressedStream = new Blob([bytes]).stream().pipeThrough(new CompressionStream("gzip"));
  const compressed = new Uint8Array(await new Response(compressedStream).arrayBuffer());
  return base64EncodeBytes(compressed);
}

function base64EncodeBytes(bytes) {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, Math.min(i + chunkSize, bytes.length));
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function json(value, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

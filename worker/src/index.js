const GITHUB_ISSUER = "https://token.actions.githubusercontent.com";
const GITHUB_JWKS = "https://token.actions.githubusercontent.com/.well-known/jwks";
const EXPECTED_AUDIENCE = "hereliesaz-workflows";
const OWNER_LOGIN = "HereLiesAz";
const OWNER_ID = "103241502";
const CENTRAL_REPOSITORY = "HereLiesAz/workflows";
const GATEWAY_WORKFLOW = "gateway.yml";
const API_VERSION = "2026-03-10";
const MAX_REQUEST_JSON_BYTES = 512 * 1024;
const MAX_WORKFLOW_DISPATCH_INPUT_CHARS = 60000;

let jwksCache;
let jwksCacheExpiresAt = 0;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "HereLiesAz/workflows gateway" });
    }

    if (request.method !== "POST" || url.pathname !== "/dispatch") {
      return new Response("Not found", { status: 404 });
    }

    try {
      if (!env.DISPATCH_TOKEN) {
        throw new HttpError(500, "Worker DISPATCH_TOKEN is not configured");
      }

      const bearer = request.headers.get("Authorization") || "";
      const match = bearer.match(/^Bearer\s+(.+)$/i);
      if (!match) {
        throw new HttpError(401, "Missing OIDC bearer token");
      }

      const claims = await verifyGitHubOidc(match[1]);
      const rawBody = await request.text();
      if (new TextEncoder().encode(rawBody).byteLength > MAX_REQUEST_JSON_BYTES) {
        throw new HttpError(413, "Dispatch payload is too large");
      }

      let body;
      try {
        body = JSON.parse(rawBody);
      } catch {
        throw new HttpError(400, "Request body is not valid JSON");
      }

      validateDispatch(body, claims);

      // workflow_dispatch has a finite input envelope. GitHub event payloads, especially
      // pull_request events, routinely exceed it when base64-encoded raw. Gzip the verified
      // request first; gateway.yml accepts both gzip and the old plain-base64 format so the
      // Worker and workflow can be deployed in either order.
      const requestB64 = await gzipBase64Utf8(rawBody);
      if (requestB64.length > MAX_WORKFLOW_DISPATCH_INPUT_CHARS) {
        throw new HttpError(413, "Compressed dispatch payload is still too large for workflow_dispatch");
      }

      const apiResponse = await fetch(
        `https://api.github.com/repos/${CENTRAL_REPOSITORY}/actions/workflows/${GATEWAY_WORKFLOW}/dispatches`,
        {
          method: "POST",
          headers: {
            "Accept": "application/vnd.github+json",
            "Authorization": `Bearer ${env.DISPATCH_TOKEN}`,
            "Content-Type": "application/json",
            "User-Agent": "HereLiesAz-workflows-cloudflare-gateway",
            "X-GitHub-Api-Version": API_VERSION,
          },
          body: JSON.stringify({
            ref: "main",
            inputs: {
              repository: body.repository,
              repository_id: String(body.repository_id),
              request_b64: requestB64,
            },
          }),
        },
      );

      if (!apiResponse.ok) {
        const detail = await apiResponse.text();
        throw new HttpError(502, `GitHub dispatch failed (${apiResponse.status}): ${detail}`);
      }

      return json({
        ok: true,
        repository: body.repository,
        repository_id: String(body.repository_id),
        source_workflow_path: body.source_workflow_path,
      }, 202);
    } catch (error) {
      if (error instanceof HttpError) {
        return json({ ok: false, error: error.message }, error.status);
      }
      console.error(error);
      return json({ ok: false, error: "Internal gateway error" }, 500);
    }
  },
};

function validateDispatch(body, claims) {
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
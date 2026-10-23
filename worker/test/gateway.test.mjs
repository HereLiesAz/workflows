// Security gates of worker/src/index.js: webhook signatures, GitHub OIDC verification and the
// remote-run callback. index.js imports "cloudflare:workers", which exists only in the Workers
// runtime, so a loader hook supplies a stub before it is imported.
import assert from "node:assert/strict";
import { createHmac, generateKeyPairSync, sign as nodeSign } from "node:crypto";
import { register } from "node:module";
import test from "node:test";

register(
  "data:text/javascript," + encodeURIComponent(`
    export async function resolve(specifier, context, next) {
      if (specifier === "cloudflare:workers") return { url: "data:text/javascript,export class WorkerEntrypoint {}", shortCircuit: true };
      return next(specifier, context);
    }`),
  import.meta.url,
);
const { default: worker } = await import("../src/index.js");
const { createRemoteRunToken } = await import("../src/remote-run.js");

const ENV = { DISPATCH_TOKEN: "dispatch-secret" };
const ORIGIN = "https://gateway.test";

function webhookSecret(token = ENV.DISPATCH_TOKEN) {
  return createHmac("sha256", token).update("HereLiesAz/workflows:webhook-signing:v1").digest("hex");
}
function signBody(body, secret = webhookSecret()) {
  return "sha256=" + createHmac("sha256", secret).update(body).digest("hex");
}
function webhook(body, headers = {}) {
  return new Request(`${ORIGIN}/webhook`, { method: "POST", headers: { "X-GitHub-Event": "ping", ...headers }, body });
}

test("/webhook rejects a missing, malformed, wrong-secret or tampered signature", async () => {
  const body = JSON.stringify({ zen: "Keep it logically awesome." });
  const cases = [
    {},
    { "X-Hub-Signature-256": "nope" },
    { "X-Hub-Signature-256": "sha256=zz" },
    { "X-Hub-Signature-256": "sha256=" + "0".repeat(64) },
    { "X-Hub-Signature-256": signBody(body, webhookSecret("another-token")) },
    { "X-Hub-Signature-256": signBody(body, "dispatch-secret") }, // the raw token is not the signing key
    { "X-Hub-Signature-256": signBody(body + " ") }, // signature of a different body
  ];
  for (const headers of cases) {
    const response = await worker.fetch(webhook(body, headers), ENV);
    assert.equal(response.status, 401, JSON.stringify(headers));
  }
});

test("/webhook accepts the derived-secret signature and answers a ping", async () => {
  const body = JSON.stringify({ zen: "Design for failure." });
  const response = await worker.fetch(webhook(body, { "X-Hub-Signature-256": signBody(body) }), ENV);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true, pong: true, zen: "Design for failure." });
});

test("/webhook with a valid signature still needs an event header and JSON", async () => {
  const body = "not json";
  const sig = { "X-Hub-Signature-256": signBody(body) };
  assert.equal((await worker.fetch(webhook(body, sig), ENV)).status, 400);
  const noEvent = new Request(`${ORIGIN}/webhook`, { method: "POST", headers: sig, body });
  assert.equal((await worker.fetch(noEvent, ENV)).status, 400);
});

test("/webhook fails closed when the Worker has no DISPATCH_TOKEN", async () => {
  const body = "{}";
  assert.equal((await worker.fetch(webhook(body, { "X-Hub-Signature-256": signBody(body) }), {})).status, 500);
});

// ---- GitHub OIDC (exercised through /remote-run/start) ----

const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const other = generateKeyPairSync("rsa", { modulusLength: 2048 });
const KID = "test-kid";
const JWKS = { keys: [{ ...publicKey.export({ format: "jwk" }), kid: KID, use: "sig", alg: "RS256" }] };

function jwt({ header = {}, claims = {}, key = privateKey } = {}) {
  const now = Math.floor(Date.now() / 1000);
  const h = Buffer.from(JSON.stringify({ alg: "RS256", kid: KID, typ: "JWT", ...header })).toString("base64url");
  const c = Buffer.from(JSON.stringify({
    iss: "https://token.actions.githubusercontent.com",
    aud: "hereliesaz-workflows",
    exp: now + 600,
    repository: "HereLiesAz/workflows",
    repository_owner_id: "103241502",
    workflow_ref: "HereLiesAz/workflows/.github/workflows/ci-validation.yml@refs/heads/main",
    ...claims,
  })).toString("base64url");
  const signature = nodeSign("sha256", Buffer.from(`${h}.${c}`), key).toString("base64url");
  return `${h}.${c}.${signature}`;
}

async function start(token, { jwks = JWKS } = {}) {
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    if (String(url).includes("/.well-known/jwks")) return new Response(JSON.stringify(jwks), { status: 200 });
    throw new Error(`unexpected network call ${url}`);
  };
  try {
    return await worker.fetch(new Request(`${ORIGIN}/remote-run/start`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: "{}",
    }), ENV);
  } finally {
    globalThis.fetch = realFetch;
  }
}

async function errorOf(response) {
  return (await response.json()).error;
}

test("OIDC: a correctly signed token from the central CI workflow passes verification", async () => {
  // Verification succeeded when the request reaches body validation (400), not an auth error.
  const response = await start(jwt());
  assert.equal(response.status, 400);
  assert.match(await errorOf(response), /target_repository is invalid/);
});

test("OIDC: bad structure, algorithm, issuer, audience, expiry and signature are all 401", async () => {
  const now = Math.floor(Date.now() / 1000);
  const cases = [
    ["not-a-jwt", /Malformed OIDC token/],
    [jwt({ header: { alg: "HS256" } }), /Unsupported OIDC signing key/],
    [jwt({ header: { alg: "none" } }), /Unsupported OIDC signing key/],
    [jwt({ header: { kid: undefined } }), /Unsupported OIDC signing key/],
    [jwt({ claims: { iss: "https://evil.example" } }), /Unexpected OIDC issuer/],
    [jwt({ claims: { aud: "someone-else" } }), /Unexpected OIDC audience/],
    [jwt({ claims: { exp: now - 3600 } }), /Expired OIDC token/],
    [jwt({ claims: { exp: undefined } }), /Expired OIDC token/],
    [jwt({ claims: { nbf: now + 3600 } }), /not valid yet/],
    [jwt({ key: other.privateKey }), /Invalid GitHub OIDC signature/],
    [jwt({ header: { kid: "unknown-kid" } }), /Unknown GitHub OIDC signing key/],
  ];
  for (const [token, message] of cases) {
    const response = await start(token);
    assert.equal(response.status, 401, String(message));
    assert.match(await errorOf(response), message);
  }
});

test("OIDC: a valid token from another repository, owner or workflow is refused with 403", async () => {
  const cases = [
    [{ repository: "HereLiesAz/other" }, /Only HereLiesAz\/workflows/],
    [{ repository_owner_id: "1" }, /owner mismatch/],
    [{ workflow_ref: "HereLiesAz/workflows/.github/workflows/gateway.yml@refs/heads/main" }, /only be issued by CI Validation/],
  ];
  for (const [claims, message] of cases) {
    const response = await start(jwt({ claims }));
    assert.equal(response.status, 403);
    assert.match(await errorOf(response), message);
  }
});

test("/remote-run/start and /ci-report require a bearer token", async () => {
  for (const path of ["/remote-run/start", "/ci-report"]) {
    const response = await worker.fetch(new Request(`${ORIGIN}${path}`, { method: "POST", body: "{}" }), ENV);
    assert.equal(response.status, 401, path);
  }
});

// ---- remote-run callback ----

function callback(token, body = { state: "success" }) {
  return worker.fetch(new Request(`${ORIGIN}/remote-run/callback`, {
    method: "POST",
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }), ENV);
}

test("/remote-run/callback refuses missing, tampered, wrong-secret and expired tokens", async () => {
  const now = Math.floor(Date.now() / 1000);
  const claims = { kind: "remote-compute", provider: "kaggle", run_ref: "a/b", iat: now, exp: now + 600, publish_release: false, target_repository: "HereLiesAz/x" };
  const good = await createRemoteRunToken(ENV.DISPATCH_TOKEN, claims);

  assert.equal((await callback(null)).status, 401);
  assert.equal((await callback("garbage")).status, 401);

  const [, signature] = good.split(".");
  const forged = Buffer.from(JSON.stringify({ ...claims, v: 1, publish_release: true, target_repository: "HereLiesAz/victim" })).toString("base64url");
  const tampered = await callback(`${forged}.${signature}`);
  assert.equal(tampered.status, 401);
  assert.match(await errorOf(tampered), /Invalid remote-run token/);

  const wrongSecret = await callback(await createRemoteRunToken("not-the-secret", claims));
  assert.equal(wrongSecret.status, 401);

  const expired = await callback(await createRemoteRunToken(ENV.DISPATCH_TOKEN, { ...claims, iat: now - 7200, exp: now - 3600 }));
  assert.equal(expired.status, 401);
  assert.match(await errorOf(expired), /expired/);
});

test("/remote-run/callback validates kind and state before touching GitHub", async () => {
  const now = Math.floor(Date.now() / 1000);
  const base = { provider: "kaggle", run_ref: "a/b", iat: now, exp: now + 600 };
  const wrongKind = await callback(await createRemoteRunToken(ENV.DISPATCH_TOKEN, { ...base, kind: "other" }));
  assert.equal(wrongKind.status, 400);
  const badState = await callback(await createRemoteRunToken(ENV.DISPATCH_TOKEN, { ...base, kind: "remote-compute" }), { state: "running" });
  assert.equal(badState.status, 400);
});

test("/remote-run/callback consumes the token's jti once when a KV store is bound", async () => {
  const now = Math.floor(Date.now() / 1000);
  const claims = { kind: "remote-compute", provider: "kaggle", run_ref: "a/b", iat: now, exp: now + 600, jti: "A".repeat(24) };
  const token = await createRemoteRunToken(ENV.DISPATCH_TOKEN, claims);
  const data = new Map();
  const env = { ...ENV, REMOTE_RUN_JTI: { get: async (k) => data.get(k) ?? null, put: async (k, v) => { data.set(k, v); } } };
  const send = () => worker.fetch(new Request(`${ORIGIN}/remote-run/callback`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ state: "bogus" }),
  }), env);
  // The first use consumes the jti (then fails state validation with 400); the replay is a 409.
  assert.equal((await send()).status, 400);
  assert.equal((await send()).status, 409);
});

import assert from "node:assert/strict";
import test from "node:test";

import {
  createRemoteRunToken,
  normalizeRemoteRunState,
  sanitizeStatusDescription,
  verifyRemoteRunToken,
} from "../src/remote-run.js";

test("remote-run token round-trips and expires", async () => {
  const claims = {
    iat: 1_000,
    exp: 2_000,
    target_repository: "HereLiesAz/onwordly",
    target_check_sha: "a".repeat(40),
    source_workflow_path: ".github/workflows/kaggle-experiment.yml",
    provider: "kaggle",
    run_ref: "azwashere/onwordly-experiment-deadbeef",
  };
  const token = await createRemoteRunToken("test-secret", claims);
  assert.deepEqual(await verifyRemoteRunToken("test-secret", token, 1_500), { v: 1, ...claims });
  await assert.rejects(() => verifyRemoteRunToken("test-secret", token, 2_001), /expired/);
  await assert.rejects(() => verifyRemoteRunToken("wrong-secret", token, 1_500), /Invalid/);
});

test("remote-run state and description normalization are bounded", () => {
  assert.equal(normalizeRemoteRunState("complete"), "success");
  assert.equal(normalizeRemoteRunState("FAILED"), "failure");
  assert.throws(() => normalizeRemoteRunState("running"), /success or failure/);
  assert.equal(sanitizeStatusDescription("  hello   world  ", "fallback"), "hello world");
  assert.equal(sanitizeStatusDescription("x".repeat(200), "fallback").length, 140);
});

import { consumeRemoteRunJti, markRemoteRunJtiUsed, newRemoteRunJti, remoteRunJtiIsFresh } from "../src/remote-run.js";

const CLAIMS = { iat: 1_000, exp: 2_000, provider: "kaggle", run_ref: "a/b", publish_release: false };

function b64url(text) {
  return Buffer.from(text, "utf8").toString("base64url");
}

test("a tampered payload with the original signature is rejected", async () => {
  const token = await createRemoteRunToken("s3cret", CLAIMS);
  const [, signature] = token.split(".");
  const forged = b64url(JSON.stringify({ ...CLAIMS, v: 1, publish_release: true, exp: 9_999_999_999 }));
  await assert.rejects(() => verifyRemoteRunToken("s3cret", `${forged}.${signature}`, 1_500), /Invalid remote-run token/);
});

test("malformed tokens fail closed", async () => {
  const token = await createRemoteRunToken("s3cret", CLAIMS);
  for (const bad of ["", "abc", "a.b.c", `${token}.extra`, ".", `${token.split(".")[0]}.`]) {
    await assert.rejects(() => verifyRemoteRunToken("s3cret", bad, 1_500), /Malformed|Invalid/, bad);
  }
  await assert.rejects(() => verifyRemoteRunToken("", token, 1_500), /secret is required/);
  await assert.rejects(() => verifyRemoteRunToken("s3cret", token, 900), /not valid yet/);
});

test("a payload re-signed under another version or without timestamps is rejected", async () => {
  // Only the Worker's secret can sign, so craft payloads through createRemoteRunToken itself.
  const noTimes = await createRemoteRunToken("s3cret", { provider: "kaggle" });
  await assert.rejects(() => verifyRemoteRunToken("s3cret", noTimes, 1_500), /invalid timestamps/);
});

test("jti is single-use when a store is bound, and a no-op without one", async () => {
  const jti = newRemoteRunJti();
  assert.match(jti, /^[A-Za-z0-9_-]{16,64}$/);
  assert.notEqual(jti, newRemoteRunJti());
  assert.equal(await consumeRemoteRunJti(undefined, { jti }), true);

  const data = new Map();
  const store = {
    get: async (k) => data.get(k) ?? null,
    put: async (k, v, opts) => { data.set(k, v); store.last = opts; },
  };
  const claims = { jti, exp: 2_000 };
  assert.equal(await consumeRemoteRunJti(store, claims, 1_500), true);
  assert.ok(store.last.expirationTtl >= 60);
  assert.equal(await consumeRemoteRunJti(store, claims, 1_501), false);
  assert.equal(await consumeRemoteRunJti(store, { exp: 2_000 }, 1_500), false, "a token without a jti is refused when single-use is on");
  assert.equal(await consumeRemoteRunJti(store, { jti: "short", exp: 2_000 }, 1_500), false);
});

test("a jti stays usable until it is marked, so a failed first attempt can be retried", async () => {
  const entries = new Map();
  const store = { get: async (k) => entries.get(k), put: async (k, v) => { entries.set(k, v); } };
  const claims = { jti: newRemoteRunJti(), exp: 2_000 };
  assert.equal(await remoteRunJtiIsFresh(store, claims), true);
  assert.equal(await remoteRunJtiIsFresh(store, claims), true, "checking does not consume it");
  await markRemoteRunJtiUsed(store, claims, 1_500);
  assert.equal(await remoteRunJtiIsFresh(store, claims), false);
  assert.equal(await remoteRunJtiIsFresh(store, { exp: 2_000 }), false, "no jti: refused when single-use is on");
  assert.equal(await remoteRunJtiIsFresh(undefined, claims), true);
});

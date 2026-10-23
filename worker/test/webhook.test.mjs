import assert from "node:assert/strict";
import { register } from "node:module";
import test from "node:test";

register("./cf-stub-loader.mjs", import.meta.url);
const { default: worker } = await import("../src/index.js");

const DISPATCH_TOKEN = "test-dispatch-token";
const OWNER = { id: 103241502, login: "HereLiesAz" };

async function sign(body, token = DISPATCH_TOKEN) {
  const hmac = async (keyText, data) => {
    const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(keyText), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    return Buffer.from(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data))).toString("hex");
  };
  // The webhook secret is itself derived from DISPATCH_TOKEN (see derivedWebhookSecret).
  const secret = await hmac(token, "HereLiesAz/workflows:webhook-signing:v1");
  return `sha256=${await hmac(secret, body)}`;
}

async function deliver({ event = "push", payload, delivery = "d-1", signature, env = {} }) {
  const body = JSON.stringify(payload);
  const headers = { "X-GitHub-Event": event, "X-GitHub-Delivery": delivery };
  if (signature !== null) headers["X-Hub-Signature-256"] = signature ?? await sign(body);
  const response = await worker.fetch(
    new Request("https://worker.test/webhook", { method: "POST", headers, body }),
    { DISPATCH_TOKEN, ...env },
  );
  return { status: response.status, body: await response.json() };
}

const unregistered = { repository: { id: 1, full_name: "HereLiesAz/not-registered", owner: OWNER }, ref: "refs/heads/main" };

function memoryKv() {
  const data = new Map();
  return { async get(k) { return data.has(k) ? data.get(k) : null; }, async put(k, v) { data.set(k, v); } };
}

test("a delivery without a signature is rejected", async () => {
  const r = await deliver({ payload: unregistered, signature: null });
  assert.equal(r.status, 401);
});

test("a delivery with a wrong signature is rejected", async () => {
  const body = JSON.stringify(unregistered);
  const r = await deliver({ payload: unregistered, signature: await sign(body, "another-token") });
  assert.equal(r.status, 401);
  const malformed = await deliver({ payload: unregistered, signature: "sha256=zz" });
  assert.equal(malformed.status, 401);
});

test("a signed ping is answered", async () => {
  const r = await deliver({ event: "ping", payload: { zen: "Keep it logically awesome." } });
  assert.equal(r.status, 200);
  assert.equal(r.body.pong, true);
});

test("a signed event from another owner is refused", async () => {
  const stranger = { repository: { id: 2, full_name: "someone/else", owner: { id: 5, login: "someone" } } };
  const r = await deliver({ payload: stranger });
  assert.equal(r.status, 403);
});

test("a signed event for an unregistered repository is acknowledged but not dispatched", async () => {
  const r = await deliver({ payload: unregistered });
  assert.equal(r.status, 202);
  assert.equal(r.body.ignored, true);
});

test("with WEBHOOK_SEEN bound, a replayed delivery id is dropped; a new id is not", async () => {
  const env = { WEBHOOK_SEEN: memoryKv() };
  const first = await deliver({ payload: unregistered, delivery: "same", env });
  assert.equal(first.body.duplicate, undefined);
  const replay = await deliver({ payload: unregistered, delivery: "same", env });
  assert.equal(replay.body.duplicate, true);
  const fresh = await deliver({ payload: unregistered, delivery: "different", env });
  assert.equal(fresh.body.duplicate, undefined);
});

test("without WEBHOOK_SEEN the same delivery id is processed every time", async () => {
  const a = await deliver({ payload: unregistered, delivery: "same" });
  const b = await deliver({ payload: unregistered, delivery: "same" });
  assert.equal(a.body.duplicate, undefined);
  assert.equal(b.body.duplicate, undefined);
});

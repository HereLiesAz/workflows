import assert from "node:assert/strict";
import test from "node:test";

import { claimOnce } from "../src/once.js";

function fakeKv() {
  const data = new Map();
  return {
    puts: [],
    async get(key) { return data.has(key) ? data.get(key) : null; },
    async put(key, value, options) { data.set(key, value); this.puts.push([key, options]); },
  };
}

test("first claim wins, replays lose", async () => {
  const kv = fakeKv();
  assert.equal(await claimOnce(kv, "delivery:1", 3600), true);
  assert.equal(await claimOnce(kv, "delivery:1", 3600), false);
  assert.equal(await claimOnce(kv, "delivery:2", 3600), true);
});

test("keys expire (KV minimum TTL is 60 s)", async () => {
  const kv = fakeKv();
  await claimOnce(kv, "a", 5);
  await claimOnce(kv, "b", 86400.9);
  assert.deepEqual(kv.puts.map(([, o]) => o.expirationTtl), [60, 86400]);
});

test("without a KV binding every call is the first", async () => {
  assert.equal(await claimOnce(undefined, "x", 60), true);
  assert.equal(await claimOnce(undefined, "x", 60), true);
});

test("a KV failure fails open", async () => {
  const broken = { async get() { throw new Error("kv down"); }, async put() { throw new Error("kv down"); } };
  assert.equal(await claimOnce(broken, "x", 60), true);
});

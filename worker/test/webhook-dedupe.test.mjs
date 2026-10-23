import assert from "node:assert/strict";
import test from "node:test";

import { isDuplicateDelivery, markDelivery } from "../src/webhook-dedupe.js";

test("without a Cache API nothing is deduplicated and nothing throws", async () => {
  assert.equal(globalThis.caches, undefined);
  await markDelivery("d1");
  assert.equal(await isDuplicateDelivery("d1"), false);
});

test("a marked delivery id is reported as a duplicate; another id is not", async () => {
  const entries = new Map();
  globalThis.caches = {
    default: {
      match: async (req) => entries.get(req.url),
      put: async (req, res) => { entries.set(req.url, res); },
    },
  };
  try {
    assert.equal(await isDuplicateDelivery("abc-123"), false);
    await markDelivery("abc-123");
    assert.equal(await isDuplicateDelivery("abc-123"), true);
    assert.equal(await isDuplicateDelivery("abc-124"), false);
  } finally {
    delete globalThis.caches;
  }
});

test("a failing cache never breaks delivery handling", async () => {
  globalThis.caches = { default: { match: async () => { throw new Error("boom"); }, put: async () => { throw new Error("boom"); } } };
  try {
    assert.equal(await isDuplicateDelivery("x"), false);
    await markDelivery("x");
  } finally {
    delete globalThis.caches;
  }
});

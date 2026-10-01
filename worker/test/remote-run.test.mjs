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

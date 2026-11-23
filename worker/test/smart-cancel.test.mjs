import assert from "node:assert/strict";
import test from "node:test";
import { duplicateIdentity, historicalAverageMs, cancelOlderDuplicates } from "../src/smart-cancel.js";

const repo = { id: 42, full_name: "HereLiesAz/demo" };
const central = { id: 12, full_name: "HereLiesAz/workflows" };
const stamp = (minutes) => new Date(Date.parse("2026-01-01T12:00:00Z") + minutes * 60_000).toISOString();
const run = (id, status, elapsed = null, extra = {}) => ({
  id, workflow_id: 14, status,
  run_started_at: elapsed === null ? null : stamp(-elapsed),
  updated_at: stamp(0),
  ...extra,
});
const passed = (id, elapsed) => run(id, "completed", elapsed, { conclusion: "success" });
const registered = [{ id: 42, repository: "HereLiesAz/demo" }, { id: 43, repository: "HereLiesAz/other" }];

test("same local workflow across branches and commits is one action; other workflow is not", () => {
  assert.equal(duplicateIdentity(repo, run(100, "queued"), registered), "42:14");
  assert.notEqual(duplicateIdentity(repo, { workflow_id: 15 }, registered), "42:14");
  assert.equal(duplicateIdentity(repo, { workflow_id: null }, registered), null);
});

test("central runs preserve target repository, action, and ignore decorative SHA", () => {
  const common = { workflow_id: 14, path: ".github/workflows/ci-validation.yml" };
  const a = { ...common, display_title: "demo · Android CI · " + "a".repeat(40) };
  const b = { ...common, display_title: "demo · Android CI · " + "b".repeat(40) };
  const other = { ...common, display_title: "other · Android CI · " + "a".repeat(40) };
  assert.equal(duplicateIdentity(central, a, registered), duplicateIdentity(central, b, registered));
  assert.notEqual(duplicateIdentity(central, a, registered), duplicateIdentity(central, other, registered));
  assert.equal(duplicateIdentity(central, { ...common, display_title: "unregistered · Android CI" }, registered), null);
  assert.equal(duplicateIdentity(central, { ...a, path: ".github/workflows/gateway.yml" }, registered), null);
  assert.equal(duplicateIdentity(central, { ...common, display_title: "Web Deploy · repository 42" }, registered), "42:14:web-deploy");
});

test("historical mean uses completed successes, not queued duration or failures", () => {
  assert.equal(historicalAverageMs([passed(8, 10), passed(7, 20), passed(6, 30)]), 1_200_000);
  assert.equal(historicalAverageMs([passed(8, 10), run(7, "completed", 1, { conclusion: "failure" })]), null);
  assert.equal(historicalAverageMs([passed(8, 10), passed(7, 20), run(6, "completed")]), null);
});

test("force-cancels pending, early running; preserves halfway, late and completed", async () => {
  const history = [
    run(99, "queued"), run(98, "pending"),
    run(97, "in_progress", 9), run(96, "in_progress", 10),
    run(95, "in_progress", 13), run(94, "completed", 1),
    passed(90, 10), passed(89, 20), passed(88, 30),
    run(87, "queued", null, { workflow_id: 15 }),
    run(110, "queued"), // newer run: never cancel
  ];
  const calls = [];
  const api = async (path, method) => {
    calls.push({ path, method });
    return path.endsWith("?per_page=100") ? { workflow_runs: history } : null;
  };
  const result = await cancelOlderDuplicates(repo, run(100, "queued"), api, registered, Date.parse(stamp(0)));
  assert.deepEqual(result.cancelled, [
    { id: 99, reason: "pending" },
    { id: 98, reason: "pending" },
    { id: 97, reason: "under-halfway" },
  ]);
  assert.deepEqual(calls.slice(1).map((x) => x.path), [99, 98, 97].map((id) =>
    `/repos/HereLiesAz/demo/actions/runs/${id}/force-cancel`));
  assert.ok(calls.slice(1).every((x) => x.method === "POST"));
});

test("missing or unusable success history preserves running work but clears pending", async () => {
  const calls = [];
  const api = async (path) => {
    calls.push(path);
    return path.endsWith("?per_page=100") ? {
      workflow_runs: [run(9, "in_progress", 1), run(8, "queued"), passed(7, 1)]
    } : null;
  };
  const result = await cancelOlderDuplicates(repo, run(10, "queued"), api, registered, Date.parse(stamp(0)));
  assert.deepEqual(result.cancelled, [{ id: 8, reason: "pending" }]);
  assert.equal(result.average_ms, null);
  assert.equal(calls.filter((s) => s.includes("/force-cancel")).length, 1);
});

test("invalid timestamps, unreliable identity, missing API history never kill running work", async () => {
  const missing = async () => ({ workflow_runs: [run(9, "in_progress", null), passed(8, 1), passed(7, 1), passed(6, 1)] });
  assert.deepEqual((await cancelOlderDuplicates(repo, run(10, "queued"), missing, registered)).cancelled, []);
  const absent = await cancelOlderDuplicates(repo, run(10, "queued"), async () => null, registered);
  assert.equal(absent.skipped, "history-unavailable");
  const unknown = await cancelOlderDuplicates(central, { ...run(10, "queued"), display_title: "other format" }, async () => { throw Error("should not call"); }, registered);
  assert.equal(unknown.skipped, "unidentified");
});

test("failed force-cancel is reported but does not block other duplicates", async () => {
  const api = async (path) => {
    if (path.endsWith("?per_page=100")) return { workflow_runs: [run(9, "queued"), run(8, "queued")] };
    if (path.includes("/runs/9/")) throw Error("conflict");
    return null;
  };
  const result = await cancelOlderDuplicates(repo, run(10, "queued"), api, registered);
  assert.deepEqual(result.cancelled, [{ id: 8, reason: "pending" }]);
  assert.equal(result.failures[0].id, 9);
});

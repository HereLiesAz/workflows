// node --test worker/test/
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  applyReport, applyWebhookEvent, ciWorkflowForEvent, CI_STATUS_RUN_HISTORY, reportFromClaims, updateLedger,
} from "../src/ci-status.js";

const consumer = { repository: "HereLiesAz/one", events: ["push"], ci: [{ path: ".github/workflows/ci.yml", name: "CI" }] };
const repository = { id: 1, full_name: "HereLiesAz/one" };
const workflow = consumer.ci[0];

test("matches only registered CI workflows", () => {
  assert.deepEqual(ciWorkflowForEvent(consumer, "workflow_run", { workflow_run: { path: ".github/workflows/ci.yml" } }), workflow);
  assert.deepEqual(ciWorkflowForEvent(consumer, "workflow_job", { workflow_job: { workflow_name: "CI" } }), workflow);
  assert.equal(ciWorkflowForEvent(consumer, "workflow_run", { workflow_run: { path: ".github/workflows/release.yml" } }), null);
  assert.equal(ciWorkflowForEvent({ events: ["push"] }, "workflow_run", { workflow_run: { path: ".github/workflows/ci.yml" } }), null);
  assert.equal(ciWorkflowForEvent(consumer, "push", {}), null);
});

test("records run and job progress, job first", () => {
  let ledger = applyWebhookEvent(null, repository, workflow, "workflow_job", {
    workflow_job: { run_id: 9, name: "test", status: "in_progress", head_sha: "abc",
      steps: [{ name: "a", status: "completed" }, { name: "b", status: "in_progress" }] },
  }, "t1");
  let run = ledger.workflows[workflow.path].runs[0];
  assert.equal(run.status, "in_progress");
  assert.equal(run.jobs.test.current_step, "b");
  assert.equal(run.jobs.test.steps_completed, 1);
  ledger = applyWebhookEvent(ledger, repository, workflow, "workflow_run", {
    workflow_run: { id: 9, run_number: 3, status: "completed", conclusion: "success", head_sha: "abc", html_url: "u" },
  }, "t2");
  run = ledger.workflows[workflow.path].runs[0];
  assert.equal(ledger.workflows[workflow.path].runs.length, 1);
  assert.equal(run.conclusion, "success");
  assert.equal(run.jobs.test.status, "in_progress");
});

test("keeps bounded newest-first history", () => {
  let ledger = null;
  for (let id = 1; id <= CI_STATUS_RUN_HISTORY + 5; id += 1) {
    ledger = applyWebhookEvent(ledger, repository, workflow, "workflow_run", { workflow_run: { id, status: "queued" } });
  }
  const runs = ledger.workflows[workflow.path].runs;
  assert.equal(runs.length, CI_STATUS_RUN_HISTORY);
  assert.equal(runs[0].run_id, CI_STATUS_RUN_HISTORY + 5);
});

test("reports trust OIDC claims, not the body", () => {
  const claims = {
    repository_owner_id: "103241502", repository_id: "1", repository: "HereLiesAz/one", run_id: "9",
    workflow_ref: "HereLiesAz/one/.github/workflows/ci.yml@refs/heads/main", workflow: "CI", sha: "abc", ref: "refs/heads/main",
  };
  const report = reportFromClaims(claims, { job: "test", summary: "12 passed", data: { passed: 12 }, repository: "evil" }, "103241502");
  assert.equal(report.workflow.path, ".github/workflows/ci.yml");
  assert.equal(report.repository.full_name, "HereLiesAz/one");
  const ledger = applyReport(null, report, "t");
  assert.equal(ledger.workflows[".github/workflows/ci.yml"].runs[0].reports.test.summary, "12 passed");
  assert.equal(ledger.workflows[".github/workflows/ci.yml"].runs[0].branch, "main");
  assert.throws(() => reportFromClaims({ ...claims, repository_owner_id: "1" }, {}, "103241502"), /owner/);
  assert.throws(() => reportFromClaims({ ...claims, workflow_ref: "Other/x/.github/workflows/ci.yml@x" }, {}, "103241502"));
});

test("updateLedger retries a conflicting write and creates the branch", async () => {
  const calls = [];
  let puts = 0;
  const api = async (path, method, body) => {
    calls.push(`${method} ${path}`);
    if (method === "GET" && path.includes("/contents/")) throw new Error("GitHub API failed (404): missing");
    if (method === "GET" && path.includes("/git/ref/")) throw new Error("GitHub API failed (404): missing");
    if (method === "POST") return { sha: "s" };
    if (method === "PUT") {
      puts += 1;
      if (puts === 1) throw new Error("GitHub API failed (409): conflict");
      assert.equal(body.branch, "ci-status");
      return {};
    }
    throw new Error("unexpected");
  };
  const result = await updateLedger(api, "HereLiesAz/workflows", 1, (ledger) =>
    applyWebhookEvent(ledger, repository, workflow, "workflow_run", { workflow_run: { id: 1, status: "queued" } }));
  assert.equal(puts, 2);
  assert.ok(calls.includes("POST /repos/HereLiesAz/workflows/git/refs"));
  assert.equal(result.repository.full_name, "HereLiesAz/one");
});

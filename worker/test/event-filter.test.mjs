// node --test worker/test/
import assert from "node:assert/strict";
import { test } from "node:test";
import { EVENT_CONSUMERS } from "../src/event-consumers.js";
import { routingDropReason, webhookDropReason } from "../src/event-filter.js";

const consumers = {
  "1": { repository: "HereLiesAz/one", events: ["create", "issue_comment", "pull_request", "push"] },
  "2": { repository: "HereLiesAz/two", events: ["push"] },
};

test("forwards events an active workflow consumes", () => {
  for (const event of ["push", "pull_request", "issue_comment", "create"]) {
    assert.equal(webhookDropReason(1, event, consumers), null, event);
  }
  assert.equal(webhookDropReason("2", "push", consumers), null);
});

test("drops events with no consumer", () => {
  for (const event of ["workflow_run", "release", "delete", "issues", "check_run", "pull_request_target"]) {
    assert.match(webhookDropReason(1, event, consumers), /No active registered workflow/, event);
  }
  assert.ok(webhookDropReason(2, "pull_request", consumers));
});

test("drops repositories that are not registered", () => {
  assert.match(webhookDropReason(3, "push", consumers), /not registered/);
  assert.ok(webhookDropReason("__proto__", "push", consumers));
  assert.ok(webhookDropReason("toString", "push", consumers));
});

test("generated map: every registered repository forwards push, never workflow_run", () => {
  const ids = Object.keys(EVENT_CONSUMERS);
  assert.ok(ids.length > 0);
  for (const id of ids) {
    assert.equal(webhookDropReason(id, "push"), null, id);
    assert.ok(webhookDropReason(id, "workflow_run") || EVENT_CONSUMERS[id].events.includes("workflow_run"));
    assert.ok(!EVENT_CONSUMERS[id].events.includes("pull_request_target"), id);
    assert.ok(!EVENT_CONSUMERS[id].events.includes("schedule"), id);
  }
});

test("push: deletions and CI-skip pushes are dropped, real pushes forwarded", async () => {
  const { pushDropReason } = await import("../src/event-filter.js");
  const main = { ref: "refs/heads/main", deleted: false, head_commit: { message: "Merge pull request #533" }, commits: [{ message: "feat: x" }, { message: "Merge pull request #533" }] };
  assert.equal(pushDropReason(main), null);
  assert.equal(pushDropReason({ ...main, commits: [] }), null);
  assert.equal(pushDropReason({}), null);
  assert.equal(pushDropReason(undefined), null);
  assert.match(pushDropReason({ ref: "refs/heads/claude/x", deleted: true, head_commit: null, commits: [] }), /deletes a ref/);
  assert.match(pushDropReason({ ...main, head_commit: { message: "chore(version): 1.48.0.1 (minor) [skip ci]" } }), /CI-skip/);
  assert.match(pushDropReason({ ...main, head_commit: null, commits: [{ message: "a [CI SKIP]" }, { message: "b [no ci]" }] }), /CI-skip/);
  // one skip-tagged commit among real ones must still build
  assert.equal(pushDropReason({ ...main, commits: [{ message: "a [skip ci]" }, { message: "b" }] }), null);
});

test("early routing preserves explicit PR actions, default branches, tags and workflow setup changes", () => {
  const map = {"1": {default_branch: "main", routing: {pull_request: [{types: ["opened", "synchronize"]}, {types: ["closed"], branches: ["release/*"]}], push: [{branches: ["main"], paths: ["src/*"]}, {tags: ["v*"]}]}}};
  const pr = (action, ref = "main") => ({action, pull_request: {base: {ref}}});
  assert.equal(routingDropReason(1, "pull_request", pr("opened"), map), null);
  assert.ok(routingDropReason(1, "pull_request", pr("closed"), map));
  assert.equal(routingDropReason(1, "pull_request", pr("closed", "release/1"), map), null);
  assert.ok(routingDropReason(1, "pull_request", pr("labeled"), map));
  const commit = path => ({added: [], modified: [path], removed: []});
  const push = (ref, path) => ({ref, repository: {default_branch: "main"}, size: 1, commits: [commit(path)], head_commit: commit(path)});
  assert.ok(routingDropReason(1, "push", push("refs/heads/feature", "src/a"), map));
  assert.equal(routingDropReason(1, "push", push("refs/heads/main", "src/a"), map), null);
  assert.equal(routingDropReason(1, "push", push("refs/heads/refs/tags/main", "src/a"), map), null);
  assert.ok(routingDropReason(1, "push", push("refs/heads/main", "README.md"), map));
  assert.equal(routingDropReason(1, "push", push("refs/heads/main", ".github/workflows/new.yml"), map), null);
  assert.equal(routingDropReason(1, "push", push("refs/tags/v1", "README.md"), map), null);
  assert.equal(routingDropReason(1, "push", {...push("refs/heads/main", "README.md"), size: 2}, map), null);
  assert.equal(routingDropReason(1, "push", {...push("refs/heads/feature", "src/a"), repository: {default_branch: "feature"}}, map), null);
  assert.equal(routingDropReason(2, "push", push("refs/heads/feature", "src/a"), map), null);
});

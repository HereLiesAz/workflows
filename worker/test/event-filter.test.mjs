// node --test worker/test/
import assert from "node:assert/strict";
import { test } from "node:test";
import { EVENT_CONSUMERS } from "../src/event-consumers.js";
import { webhookDropReason } from "../src/event-filter.js";

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

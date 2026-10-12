// node --test worker/test/
import assert from "node:assert/strict";
import { test } from "node:test";
import { normalizeTestReport, receiveTestReport, renderRun, TEST_REPORT_APPS } from "../src/test-report.js";

const key = TEST_REPORT_APPS.SphereSLAM.key;
const auth = "Basic " + btoa("testapp:" + key);

function report(over = {}) {
  return {
    packageName: "com.hereliesaz.sphereslam.testapp",
    runId: "run-12345678",
    build: "0.26.3-8c2ae09",
    libraryVersion: "0.26.3",
    appVersion: "1",
    device: { brand: "Google", model: "Pixel 8", android: "16", sdk: "36" },
    startedAt: "2026-10-12T04:00:00Z",
    updatedAt: "2026-10-12T04:05:00Z",
    checks: [
      { id: "lens", title: "Lens correction", status: "pass", evidence: "correction=FAST" },
      { id: "floor", title: "Floor lock", status: "FAIL", evidence: "no lock in 30 s | elevation -88" },
      { id: "rect", title: "Rectified match", status: "untested" },
    ],
    notes: "",
    log: "see https://example.com/secret?token=abc",
    ...over,
  };
}

function post(body, headers = {}) {
  return new Request("https://w/test-report/SphereSLAM", {
    method: "POST",
    headers: { Authorization: auth, "Content-Type": "application/json", ...headers },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
}

/** A fake GitHub holding issues and comments, recording every call. */
function fakeGitHub() {
  const issues = [];
  const comments = [];
  const calls = [];
  const api = async (path, method, body) => {
    calls.push({ path, method, body });
    if (path.startsWith("/search/issues")) {
      const label = decodeURIComponent(path).match(/label:(\S+)/)[1];
      return { items: issues.filter((i) => i.labels.includes(label)) };
    }
    let m = path.match(/\/issues\/(\d+)\/comments/);
    if (m && method === "GET") return comments.filter((c) => c.issue === Number(m[1]));
    if (m && method === "POST") {
      const c = { id: comments.length + 100, issue: Number(m[1]), body: body.body };
      comments.push(c);
      return c;
    }
    m = path.match(/\/issues\/comments\/(\d+)$/);
    if (m && method === "PATCH") {
      const c = comments.find((x) => x.id === Number(m[1]));
      c.body = body.body;
      return c;
    }
    if (path.endsWith("/issues") && method === "POST") {
      const i = { number: issues.length + 1, labels: body.labels, title: body.title };
      issues.push(i);
      return i;
    }
    throw new Error(`unexpected ${method} ${path}`);
  };
  return { api, issues, comments, calls };
}

test("a first run opens the build's issue and comments the run", async () => {
  const gh = fakeGitHub();
  const res = await receiveTestReport(post(report()), "SphereSLAM", gh.api);
  assert.equal(res.status, 200);
  assert.equal(gh.issues.length, 1);
  assert.deepEqual(gh.issues[0].labels, ["device-test", "device-test-0.26.3-8c2ae09"]);
  assert.equal(gh.comments.length, 1);
  assert.match(gh.comments[0].body, /✅ pass 1 · ❌ fail 1 · ⬜ not run 1/);
});

test("the same run reporting again updates its comment; another run adds one", async () => {
  const gh = fakeGitHub();
  await receiveTestReport(post(report()), "SphereSLAM", gh.api);
  const more = report({ checks: [{ id: "rect", title: "Rectified match", status: "PASS", evidence: "KPM_RECTIFIED at 52°" }] });
  await receiveTestReport(post(more), "SphereSLAM", gh.api);
  assert.equal(gh.issues.length, 1);
  assert.equal(gh.comments.length, 1);
  assert.match(gh.comments[0].body, /KPM_RECTIFIED at 52°/);
  await receiveTestReport(post(report({ runId: "run-abcdefgh" })), "SphereSLAM", gh.api);
  assert.equal(gh.comments.length, 2);
});

test("rejects the wrong key, an unknown repo or package, and malformed reports", async () => {
  const gh = fakeGitHub();
  assert.equal((await receiveTestReport(post(report(), { Authorization: "Basic eA==" }), "SphereSLAM", gh.api)).status, 401);
  assert.equal((await receiveTestReport(post(report()), "illumera", gh.api)).status, 404);
  assert.equal((await receiveTestReport(post(report({ packageName: "x.y" })), "SphereSLAM", gh.api)).status, 403);
  assert.equal((await receiveTestReport(post("{"), "SphereSLAM", gh.api)).status, 400);
  assert.equal((await receiveTestReport(post(report({ runId: "../x" })), "SphereSLAM", gh.api)).status, 400);
  assert.equal((await receiveTestReport(post(report({ checks: [{ id: "a", status: "MAYBE" }] })), "SphereSLAM", gh.api)).status, 400);
  assert.equal(gh.calls.length, 0);
});

test("table cells cannot break the table and URLs are redacted", () => {
  const body = renderRun(normalizeTestReport(report()));
  assert.match(body, /no lock in 30 s &#124; elevation -88/);
  assert.doesNotMatch(body, /token=abc/);
  assert.ok(body.startsWith("<!-- device-test-run:run-12345678 -->"));
});

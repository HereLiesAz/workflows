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
function fakeGitHub(afterCreate) {
  const issues = [];
  const comments = [];
  const calls = [];
  const api = async (path, method, body) => {
    calls.push({ path, method, body });
    let l = path.match(/\/issues\?labels=([^&]+)/);
    if (l && method === "GET") {
      const label = decodeURIComponent(l[1]);
      return issues.filter((i) => i.state === "open" && i.labels.includes(label)).sort((a, b) => a.number - b.number);
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
      const i = { number: issues.length + 1, labels: body.labels, title: body.title, state: "open" };
      issues.push(i);
      await afterCreate?.(i);
      return i;
    }
    m = path.match(/\/issues\/(\d+)$/);
    if (m && method === "PATCH") {
      const i = issues.find((x) => x.number === Number(m[1]));
      Object.assign(i, body);
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

test("a build's second report finds the issue its first just opened (no search-index lag)", async () => {
  const gh = fakeGitHub();
  await receiveTestReport(post(report()), "SphereSLAM", gh.api);
  await receiveTestReport(post(report({ runId: "run-abcdefgh" })), "SphereSLAM", gh.api);
  assert.equal(gh.issues.length, 1);
  assert.equal(gh.comments.length, 2);
  assert.ok(gh.calls.every((c) => !c.path.startsWith("/search/")));
});

test("two first reports racing: the newer issue closes as a duplicate and the run lands on the older", async () => {
  // While this report creates its issue, another report has already opened #1.
  let raced = false;
  const gh = fakeGitHub(async (created) => {
    if (raced) return;
    raced = true;
    created.number = 2;
    gh.issues.unshift({ number: 1, labels: created.labels, title: created.title, state: "open" });
  });
  await receiveTestReport(post(report()), "SphereSLAM", gh.api);
  const newer = gh.issues.find((i) => i.number === 2);
  assert.equal(newer.state, "closed");
  assert.equal(newer.state_reason, "duplicate");
  assert.equal(gh.comments.length, 1);
  assert.equal(gh.comments[0].issue, 1);
});

test("a long log keeps its newest lines", () => {
  const lines = Array.from({ length: 2000 }, (_, i) => `line ${i} ${"x".repeat(40)}`);
  const r = normalizeTestReport(report({ log: lines.join("\n") + "\n--- crash ---\ntrace" }));
  assert.ok(r.log.startsWith("… earlier lines cut\nline "));
  assert.ok(r.log.endsWith("--- crash ---\ntrace"));
  assert.ok(r.log.length <= 50_000 + 30);
});

test("a run near the comment limit still closes its log markup", () => {
  const lines = Array.from({ length: 2000 }, (_, i) => `line ${i} <tag> & ${"y".repeat(40)}`);
  const body = renderRun(normalizeTestReport(report({ log: lines.join("\n"), notes: "n".repeat(4_000) })));
  assert.ok(body.length <= 60_000);
  assert.ok(body.endsWith("</pre>\n</details>"));
  assert.match(body, /line 1999 &lt;tag&gt;/);
});

test("a sweep's tables render escaped, bounded and in place of the checks table", () => {
  const body = renderRun(normalizeTestReport(report({
    checks: [],
    tables: [
      { title: "Configurations", columns: ["#", "Configuration", "Locked %"], rows: [["1", "Rectify from 25° | x", "81"], ["2", "<b>baseline</b>", "64", "extra"]] },
      { title: "bad", columns: "nope", rows: [] },
    ],
  })));
  assert.match(body, /- Tuning sweep/);
  assert.doesNotMatch(body, /\| Check \| Result/);
  assert.match(body, /\*\*Configurations\*\*/);
  assert.match(body, /\| 1 \| Rectify from 25° &#124; x \| 81 \|/);
  assert.match(body, /&lt;b&gt;baseline&lt;\/b&gt; \| 64 \|$/m);
  assert.doesNotMatch(body, /bad/);
});

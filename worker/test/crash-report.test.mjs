import assert from "node:assert/strict";
import test from "node:test";

import { CRASH_REPORT_APPS, constantTimeEqual, escapeHtml, markdownText, receiveCrashReport, redact, singleLine } from "../src/crash-report.js";

const AUTH = "Basic " + Buffer.from(`acra:${CRASH_REPORT_APPS.illumera.key}`).toString("base64");
const GOOD = {
  PACKAGE_NAME: "com.hereliesaz.illumera",
  STACK_TRACE: "java.lang.IllegalStateException: boom\n\tat a.B.c(B.kt:12)\n",
  APP_VERSION_NAME: "1.2.3",
};

function req(body, { auth = AUTH, headers = {} } = {}) {
  return new Request("https://w/crash-report/illumera", {
    method: "POST",
    headers: { ...(auth ? { Authorization: auth } : {}), ...headers },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
}

function github({ existing = null } = {}) {
  const calls = [];
  return {
    calls,
    fn: async (path, method, body) => {
      calls.push({ path, method, body });
      if (path.startsWith("/search/issues")) return { items: existing ? [existing] : [] };
      return {};
    },
  };
}

test("unknown repositories and prototype keys are 404", async () => {
  const gh = github();
  for (const name of ["nope", "__proto__", "constructor", "toString"]) {
    assert.equal((await receiveCrashReport(req(GOOD), name, gh.fn)).status, 404, name);
  }
  assert.equal(gh.calls.length, 0);
});

test("missing or wrong credentials are 401 before any body handling", async () => {
  const gh = github();
  assert.equal((await receiveCrashReport(req(GOOD, { auth: "" }), "illumera", gh.fn)).status, 401);
  assert.equal((await receiveCrashReport(req(GOOD, { auth: "Basic " + btoa("acra:wrong") }), "illumera", gh.fn)).status, 401);
  // aive's key must not open illumera
  assert.equal((await receiveCrashReport(req(GOOD, { auth: "Basic " + btoa(`acra:${CRASH_REPORT_APPS.aive.key}`) }), "illumera", gh.fn)).status, 401);
  assert.equal(gh.calls.length, 0);
});

test("rejects oversized, non-JSON, non-object and wrong-package reports", async () => {
  const gh = github();
  assert.equal((await receiveCrashReport(req(GOOD, { headers: { "Content-Length": String(300 * 1024) } }), "illumera", gh.fn)).status, 413);
  assert.equal((await receiveCrashReport(req("x".repeat(300 * 1024)), "illumera", gh.fn)).status, 413);
  assert.equal((await receiveCrashReport(req("{nope"), "illumera", gh.fn)).status, 400);
  assert.equal((await receiveCrashReport(req("[1,2]"), "illumera", gh.fn)).status, 400);
  assert.equal((await receiveCrashReport(req({ ...GOOD, PACKAGE_NAME: "com.evil" }), "illumera", gh.fn)).status, 403);
  assert.equal((await receiveCrashReport(req({ PACKAGE_NAME: GOOD.PACKAGE_NAME }), "illumera", gh.fn)).status, 400);
  assert.equal(gh.calls.length, 0);
});

test("a new crash opens one labeled issue on the app's own repository", async () => {
  const gh = github();
  const response = await receiveCrashReport(req(GOOD), "illumera", gh.fn);
  assert.equal(response.status, 200);
  const create = gh.calls.find((c) => c.method === "POST");
  assert.equal(create.path, "/repos/HereLiesAz/illumera/issues");
  assert.ok(create.body.labels.includes("crash-report"));
  assert.ok(create.body.labels.some((l) => /^crash-[0-9a-f]{12}$/.test(l)));
  assert.match(create.body.title, /^Crash: java\.lang\.IllegalStateException: boom/);
});

test("the same crash comments on the open issue instead of filing another", async () => {
  const gh = github({ existing: { number: 42 } });
  assert.equal((await receiveCrashReport(req(GOOD), "illumera", gh.fn)).status, 200);
  const post = gh.calls.find((c) => c.method === "POST");
  assert.equal(post.path, "/repos/HereLiesAz/illumera/issues/42/comments");
});

test("line numbers do not change the dedupe signature, the exception does", async () => {
  const labels = [];
  for (const trace of ["E: x\n\tat a.B.c(B.kt:12)", "E: x\n\tat a.B.c(B.kt:99)", "F: y\n\tat a.B.c(B.kt:12)"]) {
    const gh = github();
    await receiveCrashReport(req({ ...GOOD, STACK_TRACE: trace }), "illumera", gh.fn);
    labels.push(gh.calls.find((c) => c.method === "POST").body.labels[1]);
  }
  assert.equal(labels[0], labels[1]);
  assert.notEqual(labels[0], labels[2]);
});

test("a GitHub failure propagates to the router, which answers generically", async () => {
  const failing = async () => { throw new Error("secret detail from GitHub"); };
  await assert.rejects(() => receiveCrashReport(req(GOOD), "illumera", failing), /secret detail/);
});

test("redact keeps only scheme and host of URLs and drops magnet links", () => {
  assert.equal(redact("see https://user:pw@host.example/path/x?token=abc#f now"), "see https://host.example/<redacted> now");
  assert.equal(redact("magnet:?xt=urn:btih:abc&dn=x"), "magnet:<redacted>");
});

test("issue text is escaped against markdown and HTML injection", () => {
  assert.equal(escapeHtml(`<img src=x onerror="a">&'`), "&lt;img src=x onerror=&quot;a&quot;&gt;&amp;&#39;");
  assert.equal(singleLine("a\r\nb\u0000c", 50), "a b c");
  assert.equal(markdownText("[x](http://e)"), "\\[x\\]\\(http://e\\)");
});

test("constantTimeEqual compares by value", async () => {
  assert.equal(await constantTimeEqual("abc", "abc"), true);
  assert.equal(await constantTimeEqual("abc", "abd"), false);
  assert.equal(await constantTimeEqual("abc", "abcd"), false);
});

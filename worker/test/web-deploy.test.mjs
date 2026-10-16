// node --test worker/test/
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  pagesProjectName,
  pagesSiteUrl,
  receiveWebDeploy,
  WEB_DEPLOY_STATUS_CONTEXT,
  WEB_DEPLOY_WORKFLOW,
} from "../src/web-deploy.js";

const SHA = "a".repeat(40);
const OWNER = { id: 103241502, login: "HereLiesAz" };
const REPO = { id: 123456789, name: "my-site", full_name: "HereLiesAz/my-site", owner: OWNER, private: true };

function post(body, token = "user-token") {
  return new Request("https://w/web-deploy", {
    method: "POST",
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), "Content-Type": "application/json" },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
}

/** GitHub as the App and as the caller, recording every call. */
function fakes({ caller = { status: 200, body: { ...REPO, permissions: { push: true } } }, app = REPO } = {}) {
  const calls = [];
  const callerCalls = [];
  return {
    calls,
    callerCalls,
    deps: {
      appApi: async (path, method = "GET", body, allowEmpty) => {
        calls.push({ path, method, body, allowEmpty });
        if (path === `/repos/${REPO.full_name}`) return app;
        if (path.startsWith(`/repos/${REPO.full_name}/commits/`)) return { sha: SHA };
        if (path.endsWith("/dispatches")) return null;
        throw new Error(`unexpected App call ${path}`);
      },
      callerApi: async (token, path) => {
        callerCalls.push({ token, path });
        return caller;
      },
    },
  };
}

test("pagesProjectName is a valid, distinct, bounded Pages project name", () => {
  assert.equal(pagesProjectName("my-site", 123456789), "ideaz-my-site-21i3v9");
  assert.notEqual(pagesProjectName("My.App", 1), pagesProjectName("my-app", 2));
  const long = pagesProjectName("x".repeat(200) + "-", 999999999999);
  assert.ok(long.length <= 58, long);
  assert.match(long, /^[a-z0-9]+(-[a-z0-9]+)*$/);
  assert.match(pagesProjectName("---", 5), /^ideaz-5$/);
  assert.throws(() => pagesProjectName("a", "1; rm"));
});

test("dispatches the central workflow for a pushed commit and names the status to poll", async () => {
  const { deps, calls, callerCalls } = fakes();
  const response = await receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: SHA.toUpperCase() }), deps);
  assert.equal(response.status, 202);
  const result = await response.json();
  const project = pagesProjectName("my-site", REPO.id);
  assert.deepEqual(result, {
    ok: true,
    repository: "HereLiesAz/my-site",
    sha: SHA,
    status_context: WEB_DEPLOY_STATUS_CONTEXT,
    site_url: pagesSiteUrl(project),
  });
  assert.deepEqual(callerCalls, [{ token: "user-token", path: "/repos/HereLiesAz/my-site" }]);
  const dispatch = calls.find((c) => c.method === "POST");
  assert.equal(dispatch.path, `/repos/HereLiesAz/workflows/actions/workflows/${WEB_DEPLOY_WORKFLOW}/dispatches`);
  assert.deepEqual(dispatch.body, {
    ref: "main",
    inputs: {
      target_repository: "HereLiesAz/my-site",
      target_repository_id: "123456789",
      target_sha: SHA,
      pages_project: project,
    },
  });
  // The caller's token never reaches the App calls.
  assert.ok(!JSON.stringify(calls).includes("user-token"));
});

test("rejects a missing token, bad input and oversized bodies before calling GitHub", async () => {
  const { deps, calls, callerCalls } = fakes();
  assert.equal((await receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: SHA }, ""), deps)).status, 401);
  assert.equal((await receiveWebDeploy(post("{nope"), deps)).status, 400);
  assert.equal((await receiveWebDeploy(post({ repository: "../etc", sha: SHA }), deps)).status, 400);
  assert.equal((await receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: "main" }), deps)).status, 400);
  assert.equal((await receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: SHA, pad: "x".repeat(20000) }), deps)).status, 413);
  assert.deepEqual(calls, []);
  assert.deepEqual(callerCalls, []);
});

test("refuses a token that cannot push, cannot see the repository, or is invalid", async () => {
  for (const [caller, status] of [
    [{ status: 200, body: { ...REPO, permissions: { push: false, pull: true } } }, 403],
    [{ status: 404, body: null }, 403],
    [{ status: 401, body: null }, 401],
  ]) {
    const { deps, calls } = fakes({ caller });
    const response = await receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: SHA }), deps);
    assert.equal(response.status, status);
    assert.deepEqual(calls, [], "nothing is dispatched");
  }
});

test("serves only repositories owned by the central owner", async () => {
  const other = { ...REPO, full_name: "someone/my-site", owner: { id: 1, login: "someone" } };
  const { deps, calls } = fakes({ caller: { status: 200, body: { ...other, permissions: { push: true } } } });
  const response = await receiveWebDeploy(post({ repository: "someone/my-site", sha: SHA }), deps);
  assert.equal(response.status, 403);
  assert.match((await response.json()).error, /owned by HereLiesAz/);
  assert.deepEqual(calls, []);
});

test("refuses when the App sees a different repository than the caller", async () => {
  const { deps, calls } = fakes({ app: { ...REPO, id: 42 } });
  const response = await receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: SHA }), deps);
  assert.equal(response.status, 409);
  assert.ok(!calls.some((c) => c.method === "POST"));
});

test("an unpushed commit is not dispatched", async () => {
  const { deps, calls } = fakes();
  deps.appApi = async (path, method = "GET") => {
    calls.push({ path, method });
    if (path === `/repos/${REPO.full_name}`) return REPO;
    throw new Error("GitHub API failed (422)");
  };
  await assert.rejects(receiveWebDeploy(post({ repository: "HereLiesAz/my-site", sha: SHA }), deps), /422/);
  assert.ok(!calls.some((c) => c.method === "POST"));
});

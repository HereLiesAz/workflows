// Device test report relay: an app's on-device test run (checks it graded itself, plus the
// tester's verdicts on the visual ones) becomes a GitHub issue comment on the app's repository.
// One issue per tested build (labelled `device-test-<build>`), one comment per run; a run that
// reports again (more checks decided) updates its own comment instead of adding another.
//
// Same trust model as crash-report.js: the per-app key ships in a public APK, so it is a spam
// filter, not a secret; the bounds are the allowlist, the package match, size limits, sanitizing
// and the fixed comment shape.

import { constantTimeEqual, escapeHtml, markdownText, redact, singleLine } from "./crash-report.js";

const OWNER = "HereLiesAz";
const MAX_REPORT_BYTES = 128 * 1024;
const MAX_CHECKS = 100;
const MAX_FIELD_CHARS = 300;
const MAX_EVIDENCE_CHARS = 1_000;
const MAX_LOG_CHARS = 50_000;
const MAX_GITHUB_BODY_CHARS = 60_000;
const STATUSES = { PASS: "✅ pass", FAIL: "❌ fail", UNTESTED: "⬜ not run", SKIPPED: "➖ skipped" };

// repository name -> the app allowed to report into it.
export const TEST_REPORT_APPS = {
  SphereSLAM: {
    packages: ["com.hereliesaz.sphereslam.testapp"],
    key: "sphereslam-test-reports-v1",
  },
};

export async function receiveTestReport(request, repoName, githubRequest) {
  const app = Object.prototype.hasOwnProperty.call(TEST_REPORT_APPS, repoName) ? TEST_REPORT_APPS[repoName] : null;
  if (!app) return text("Not found", 404);
  const expected = "Basic " + btoa("testapp:" + app.key);
  if (!(await constantTimeEqual(request.headers.get("Authorization") || "", expected))) {
    return text("Unauthorized", 401);
  }
  const declared = Number(request.headers.get("Content-Length") || "0");
  if (Number.isFinite(declared) && declared > MAX_REPORT_BYTES) return text("Payload too large", 413);
  let raw;
  try {
    raw = await request.arrayBuffer();
  } catch {
    return text("Invalid request body", 400);
  }
  if (raw.byteLength > MAX_REPORT_BYTES) return text("Payload too large", 413);
  let parsed;
  try {
    parsed = JSON.parse(new TextDecoder().decode(raw));
  } catch {
    return text("Invalid JSON", 400);
  }
  const report = normalizeTestReport(parsed);
  if (!report) return text("Invalid report", 400);
  if (!app.packages.includes(report.packageName)) return text("Unknown package", 403);

  await fileRun(report, `${OWNER}/${repoName}`, githubRequest);
  return text("OK", 200);
}

/** The validated, bounded report, or null when its shape is wrong. */
export function normalizeTestReport(parsed) {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
  const runId = clean(parsed.runId, 64);
  const build = clean(parsed.build, 64);
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(runId)) return null;
  if (!/^[A-Za-z0-9._-]{1,64}$/.test(build)) return null;
  if (!Array.isArray(parsed.checks) || parsed.checks.length > MAX_CHECKS) return null;
  const checks = [];
  for (const c of parsed.checks) {
    if (!c || typeof c !== "object") return null;
    const status = String(c.status || "").toUpperCase();
    if (!Object.prototype.hasOwnProperty.call(STATUSES, status)) return null;
    checks.push({
      id: clean(c.id, 64),
      title: clean(c.title, MAX_FIELD_CHARS),
      status,
      evidence: clean(c.evidence, MAX_EVIDENCE_CHARS),
    });
  }
  const device = parsed.device && typeof parsed.device === "object" ? parsed.device : {};
  return {
    packageName: clean(parsed.packageName, 120),
    runId,
    build,
    libraryVersion: clean(parsed.libraryVersion, 40),
    appVersion: clean(parsed.appVersion, 40),
    device: {
      brand: clean(device.brand, 60),
      model: clean(device.model, 60),
      android: clean(device.android, 20),
      sdk: clean(device.sdk, 10),
    },
    startedAt: clean(parsed.startedAt, 40),
    updatedAt: clean(parsed.updatedAt, 40),
    notes: clean(parsed.notes, 4_000),
    checks,
    log: tail(redact(typeof parsed.log === "string" ? parsed.log : ""), MAX_LOG_CHARS),
  };
}

/** The run's comment body; the marker lets a later report of the same run replace it. */
export function renderRun(report) {
  const counts = {};
  for (const c of report.checks) counts[c.status] = (counts[c.status] || 0) + 1;
  const summary = Object.keys(STATUSES).filter((s) => counts[s]).map((s) => `${STATUSES[s]} ${counts[s]}`).join(" · ");
  const d = report.device;
  const lines = [
    marker(report.runId),
    `**Run** \`${report.runId}\` — ${markdownText(d.brand)} ${markdownText(d.model)}, Android ${markdownText(d.android)} (SDK ${markdownText(d.sdk)})`,
    `- Library ${markdownText(report.libraryVersion)}, build \`${report.build}\`, app ${markdownText(report.appVersion)}`,
    `- Started ${markdownText(report.startedAt)}, last update ${markdownText(report.updatedAt)}`,
    `- ${summary || "no checks"}`,
    "",
    "| Check | Result | Evidence |",
    "|---|---|---|",
    ...report.checks.map((c) => `| ${cell(c.title || c.id)} | ${STATUSES[c.status]} | ${cell(c.evidence)} |`),
  ];
  if (report.notes) lines.push("", "**Notes**", "", `<pre>${escapeHtml(report.notes)}</pre>`);
  const head = lines.join("\n").slice(0, MAX_GITHUB_BODY_CHARS);
  if (!report.log) return head;
  // The log gets what room is left, newest lines kept, so the markup around it always closes.
  const open = "\n\n<details><summary>Log</summary>\n\n<pre>";
  const close = "</pre>\n</details>";
  const room = MAX_GITHUB_BODY_CHARS - head.length - open.length - close.length;
  if (room < 200) return head;
  let log = escapeHtml(report.log);
  if (log.length > room) log = escapeHtml(tail(report.log, Math.floor(room / 2)));
  while (log.length > room) log = log.slice(log.indexOf("\n") + 1 || log.length);
  return head + open + log + close;
}

async function fileRun(report, repoPath, githubRequest) {
  const label = `device-test-${report.build}`.slice(0, 50);
  const body = renderRun(report);
  let number = await oldestIssue(repoPath, label, githubRequest);
  if (number == null) {
    const issue = await githubRequest(`/repos/${repoPath}/issues`, "POST", {
      title: `Device test: ${singleLine(report.libraryVersion || "unversioned", 40)} (${report.build})`,
      body: `Automatically reported on-device test runs of build \`${report.build}\`. One comment per run, updated as the run progresses.`,
      labels: ["device-test", label],
    });
    if (!issue || !Number.isSafeInteger(Number(issue.number))) return;
    number = Number(issue.number);
    // Two first reports of one build can both get here; the older issue wins and the newer closes.
    const oldest = await oldestIssue(repoPath, label, githubRequest);
    if (oldest != null && oldest < number) {
      await githubRequest(`/repos/${repoPath}/issues/${number}`, "PATCH", {
        state: "closed",
        state_reason: "duplicate",
        body: `Duplicate of #${oldest}: reports of build \`${report.build}\` go there.`,
      });
      number = oldest;
    }
  }
  const comments = await githubRequest(`/repos/${repoPath}/issues/${number}/comments?per_page=100`, "GET");
  const mine = Array.isArray(comments) ? comments.find((c) => typeof c?.body === "string" && c.body.startsWith(marker(report.runId))) : null;
  if (mine && Number.isSafeInteger(Number(mine.id))) {
    await githubRequest(`/repos/${repoPath}/issues/comments/${Number(mine.id)}`, "PATCH", { body });
  } else {
    await githubRequest(`/repos/${repoPath}/issues/${number}/comments`, "POST", { body });
  }
}

/**
 * The build's issue (the lowest-numbered open one with [label]), or null. Read from the issues
 * listing, not search: the search index lags by seconds to a minute, so a run's second report used
 * to miss the issue its first had just opened and open another.
 */
async function oldestIssue(repoPath, label, githubRequest) {
  const listed = await githubRequest(
    `/repos/${repoPath}/issues?labels=${encodeURIComponent(label)}&state=open&sort=created&direction=asc&per_page=10`,
    "GET",
  );
  const numbers = (Array.isArray(listed) ? listed : [])
    .filter((i) => !i?.pull_request)
    .map((i) => Number(i?.number))
    .filter((n) => Number.isSafeInteger(n));
  return numbers.length ? Math.min(...numbers) : null;
}

function marker(runId) {
  return `<!-- device-test-run:${runId} -->`;
}

function clean(value, max) {
  if (value == null) return "";
  return redact(singleLine(typeof value === "string" ? value : String(value), max));
}

/** The last [max] characters from a line start: the newest log lines (and a crash trace, appended last). */
function tail(log, max) {
  if (log.length <= max) return log;
  const cut = log.slice(-max);
  const nl = cut.indexOf("\n");
  return "… earlier lines cut\n" + (nl >= 0 ? cut.slice(nl + 1) : cut);
}

function cell(value) {
  return escapeHtml(value || "").replace(/\|/g, "&#124;");
}

function text(body, status) {
  return new Response(body, { status });
}

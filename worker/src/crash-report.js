// Crash/ANR report relay: turns ACRA JSON reports into deduplicated GitHub issues on
// the reporting app's own repository. Ported from HereLiesAz/illumera's standalone
// cloudflare-worker so reports use this Worker's GitHub App installation token and
// deploy with it, instead of a separately provisioned worker and PAT.
//
// The app authenticates with a per-app key. That key ships inside a public APK, so it
// is a spam filter, not a secret; the real bounds are the allowlist, the package-name
// match, size limits, sanitizing, and per-signature deduplication.

const OWNER = "HereLiesAz";
const MAX_REPORT_BYTES = 256 * 1024;
const MAX_FIELD_CHARS = 2_000;
const MAX_STACK_CHARS = 40_000;
const MAX_GITHUB_BODY_CHARS = 60_000;

// repository name -> the app allowed to report into it.
export const CRASH_REPORT_APPS = {
  illumera: {
    packages: ["com.hereliesaz.illumera"],
    key: "illumera-crash-reports-v1",
  },
};

export async function receiveCrashReport(request, repoName, githubRequest) {
  const app = Object.prototype.hasOwnProperty.call(CRASH_REPORT_APPS, repoName)
    ? CRASH_REPORT_APPS[repoName]
    : null;
  if (!app) return text("Not found", 404);

  const expected = "Basic " + btoa("acra:" + app.key);
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
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return text("Invalid report", 400);

  const report = sanitizeReport(parsed);
  if (!app.packages.includes(report.PACKAGE_NAME)) return text("Unknown package", 403);
  if (!report.STACK_TRACE) return text("Missing stack trace", 400);

  const filed = await fileIssue(report, `${OWNER}/${repoName}`, githubRequest);
  return filed ? text("OK", 200) : text("GitHub relay failed", 502);
}

async function fileIssue(report, repoPath, githubRequest) {
  const stackTrace = field(report.STACK_TRACE, "No stack trace", MAX_STACK_CHARS);
  const firstLine = stackTrace.split("\n")[0] || "";
  const kind = /ApplicationNotResponding/.test(firstLine) ? "ANR" : /HandledError/.test(firstLine) ? "Error" : "Crash";
  const signature = await crashSignature(stackTrace);
  const dedupeLabel = `crash-${signature}`;
  const headline = singleLine(stackTrace.split("\n")[0] || "Unknown exception", 180);

  const details = [
    `**Occurrence** — ${markdownText(field(report.USER_CRASH_DATE))}`,
    `- App version: \`${markdownCode(field(report.APP_VERSION_NAME))}\` (${markdownText(field(report.APP_VERSION_CODE))})`,
    `- Device: ${markdownText(field(report.BRAND))} ${markdownText(field(report.PHONE_MODEL))}, Android ${markdownText(field(report.ANDROID_VERSION))}`,
    `- Memory: ${markdownText(field(report.AVAILABLE_MEM_SIZE))} available / ${markdownText(field(report.TOTAL_MEM_SIZE))} total`,
  ];
  if (report.CUSTOM_DATA) {
    details.push("", "<details><summary>Context</summary>", "", `<pre>${escapeHtml(report.CUSTOM_DATA)}</pre>`, "</details>");
  }
  details.push("", "<details><summary>Stack trace</summary>", "", `<pre>${escapeHtml(stackTrace)}</pre>`, "</details>");
  const occurrence = limit(details.join("\n"));

  const query = encodeURIComponent(`repo:${repoPath} label:${dedupeLabel} state:open`);
  const found = await githubRequest(`/search/issues?q=${query}`, "GET");
  const existing = found?.items?.[0];
  if (existing && Number.isSafeInteger(Number(existing.number))) {
    await githubRequest(`/repos/${repoPath}/issues/${Number(existing.number)}/comments`, "POST", { body: occurrence });
    return true;
  }

  await githubRequest(`/repos/${repoPath}/issues`, "POST", {
    title: `${kind}: ${headline}`.slice(0, 250),
    body: limit(`Automatically reported ${kind.toLowerCase()}.\n\n${occurrence}`),
    labels: ["crash-report", dedupeLabel],
  });
  return true;
}

function sanitizeReport(report) {
  const out = {};
  for (const [key, value] of Object.entries(report)) {
    if (!/^[A-Z0-9_]{1,80}$/.test(key)) continue;
    const max = key === "STACK_TRACE" || key === "CUSTOM_DATA" ? MAX_STACK_CHARS : MAX_FIELD_CHARS;
    out[key] = redact(stringify(value)).slice(0, max);
  }
  return out;
}

// Issues are public and stream URLs can carry account tokens (debrid links, addon
// configs): keep only scheme and host of any URL, and drop magnet links entirely.
const URL_RE = /\b([a-zA-Z][a-zA-Z0-9+.-]*:\/\/)(?:[^@/\s?#]*@)?([^/\s?#@]+)[^\s"')]*/g;
const MAGNET_RE = /magnet:\?\S+/g;

export function redact(text) {
  return text.replace(MAGNET_RE, "magnet:<redacted>").replace(URL_RE, "$1$2/<redacted>");
}

function stringify(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return "[unserializable]";
  }
}

function field(value, fallback = "unknown", max = MAX_FIELD_CHARS) {
  const t = stringify(value).trim();
  return (t || fallback).slice(0, max);
}

function singleLine(value, max) {
  return stringify(value).replace(/[\r\n\u0000-\u001f\u007f]+/g, " ").trim().slice(0, max);
}

function markdownText(value) {
  return singleLine(value, MAX_FIELD_CHARS).replace(/[\\`*_{}\[\]()#+.!|>-]/g, "\\$&");
}

function markdownCode(value) {
  return singleLine(value, MAX_FIELD_CHARS).replace(/`/g, "'");
}

function escapeHtml(value) {
  return stringify(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function limit(value) {
  return stringify(value).slice(0, MAX_GITHUB_BODY_CHARS);
}

function text(body, status) {
  return new Response(body, { status });
}

async function constantTimeEqual(left, right) {
  const enc = new TextEncoder();
  const [a, b] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(left)),
    crypto.subtle.digest("SHA-256", enc.encode(right)),
  ]);
  const x = new Uint8Array(a);
  const y = new Uint8Array(b);
  let diff = 0;
  for (let i = 0; i < x.length; i += 1) diff |= x[i] ^ y[i];
  return diff === 0;
}

/** Short, stable signature: hash of the exception line + top frames, line numbers dropped. */
async function crashSignature(stackTrace) {
  const normalized = stackTrace
    .split("\n")
    .slice(0, 6)
    .map((line) => line.replace(/:\d+\)?$/, "").trim())
    .join("\n");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 12);
}

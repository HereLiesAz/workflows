/**
 * CI status ledger.
 *
 * Target repositories run their own CI; nothing here can start, queue or block it. This module only
 * records what those runs report, so HereLiesAz/workflows holds one place to watch every project.
 *
 * Two transports feed the same ledger:
 * - the repository webhook already registered for every target (`workflow_run` / `workflow_job`),
 *   for workflows the registry marks `ci: true` — no target code, no target credentials;
 * - an optional, non-blocking `HereLiesAz/workflows/.github/actions/ci-report` step, authenticated by
 *   the run's own GitHub OIDC token, for a custom summary and data.
 *
 * The ledger lives on the orphan branch `ci-status` (no workflow files, so its commits start nothing):
 * one `repositories/<repository_id>.json` per target. `.github/workflows/ci-status-dashboard.yml`
 * renders `README.md` on that branch from those files.
 */

export const CI_STATUS_BRANCH = "ci-status";
export const CI_STATUS_RUN_HISTORY = 20;
const MAX_REPORT_SUMMARY_CHARS = 2000;
const MAX_REPORT_DATA_CHARS = 8000;
const MAX_WRITE_ATTEMPTS = 6;

/**
 * The registered CI workflow a webhook event belongs to, or null.
 * `consumer` is the repository's EVENT_CONSUMERS entry; `ci` lists `{path, name}`.
 * workflow_run carries the workflow path; workflow_job carries only the workflow name.
 */
export function ciWorkflowForEvent(consumer, eventName, event) {
  const ci = Array.isArray(consumer?.ci) ? consumer.ci : [];
  if (ci.length === 0 || !event || typeof event !== "object") return null;
  if (eventName === "workflow_run") {
    const path = String(event.workflow_run?.path || "").replace(/@.*$/, "");
    return ci.find((entry) => entry.path === path) || null;
  }
  if (eventName === "workflow_job") {
    const name = String(event.workflow_job?.workflow_name || "");
    return ci.find((entry) => entry.name === name) || null;
  }
  return null;
}

function emptyLedger(repository) {
  return {
    schema: 1,
    repository: { id: Number(repository.id), full_name: String(repository.full_name || "") },
    updated_at: "",
    workflows: {},
  };
}

/** Find or create the run record (newest first), trimming history. */
function runRecord(ledger, workflow, runId, now) {
  const workflows = ledger.workflows;
  const entry = workflows[workflow.path] ||= { name: workflow.name, runs: [] };
  entry.name = workflow.name || entry.name;
  let run = entry.runs.find((item) => String(item.run_id) === String(runId));
  if (!run) {
    run = { run_id: Number(runId), jobs: {}, reports: {}, created_at: now };
    entry.runs.unshift(run);
    entry.runs.sort((a, b) => Number(b.run_id) - Number(a.run_id));
    entry.runs.length = Math.min(entry.runs.length, CI_STATUS_RUN_HISTORY);
  }
  return run;
}

/** Apply one verified workflow_run / workflow_job webhook to a ledger. Pure apart from `now`. */
export function applyWebhookEvent(ledger, repository, workflow, eventName, event, now = new Date().toISOString()) {
  const next = ledger || emptyLedger(repository);
  if (eventName === "workflow_run") {
    const source = event.workflow_run || {};
    const run = runRecord(next, workflow, source.id, now);
    Object.assign(run, {
      run_number: source.run_number ?? run.run_number,
      run_attempt: source.run_attempt ?? run.run_attempt,
      event: source.event ?? run.event,
      branch: source.head_branch ?? run.branch,
      sha: source.head_sha ?? run.sha,
      status: source.status ?? run.status,
      conclusion: source.conclusion ?? null,
      html_url: source.html_url ?? run.html_url,
      started_at: source.run_started_at ?? run.started_at,
      updated_at: source.updated_at || now,
    });
  } else if (eventName === "workflow_job") {
    const source = event.workflow_job || {};
    const run = runRecord(next, workflow, source.run_id, now);
    run.sha ||= source.head_sha;
    run.branch ||= source.head_branch;
    // A job event can beat its run's first workflow_run event; keep the run visibly in progress.
    if (!run.status && source.status) run.status = source.status === "completed" ? "in_progress" : source.status;
    const steps = Array.isArray(source.steps) ? source.steps : [];
    run.jobs[String(source.name || source.id)] = {
      status: source.status ?? null,
      conclusion: source.conclusion ?? null,
      html_url: source.html_url ?? null,
      started_at: source.started_at ?? null,
      completed_at: source.completed_at ?? null,
      steps_completed: steps.filter((step) => step?.status === "completed").length,
      steps_total: steps.length,
      current_step: (steps.find((step) => step?.status === "in_progress") || {}).name ?? null,
    };
    run.updated_at = now;
  } else {
    return next;
  }
  next.updated_at = now;
  return next;
}

/**
 * Validate a ci-report body against the OIDC claims of the run that sent it.
 * The token, not the body, says which repository/workflow/run is reporting.
 */
export function reportFromClaims(claims, body, ownerId) {
  if (String(claims.repository_owner_id || "") !== String(ownerId)) {
    throw new Error("OIDC repository owner is not HereLiesAz");
  }
  const repositoryId = String(claims.repository_id || "");
  const fullName = String(claims.repository || "");
  const workflowRef = String(claims.workflow_ref || "");
  const runId = String(claims.run_id || "");
  const prefix = `${fullName}/`;
  if (!repositoryId || !fullName || !runId || !workflowRef.startsWith(prefix)) {
    throw new Error("OIDC token lacks repository, run or workflow claims");
  }
  const path = workflowRef.slice(prefix.length).replace(/@.*$/, "");
  const payload = body && typeof body === "object" ? body : {};
  const summary = String(payload.summary || "").slice(0, MAX_REPORT_SUMMARY_CHARS);
  let data = payload.data ?? null;
  if (data !== null && JSON.stringify(data).length > MAX_REPORT_DATA_CHARS) {
    data = { truncated: true };
  }
  return {
    repository: { id: Number(repositoryId), full_name: fullName },
    workflow: { path, name: String(claims.workflow || path) },
    run_id: runId,
    run_attempt: String(claims.run_attempt || ""),
    sha: String(claims.sha || ""),
    ref: String(claims.ref || ""),
    event: String(claims.event_name || ""),
    job: String(payload.job || claims.job_workflow_ref || "report").slice(0, 200),
    status: String(payload.status || "").slice(0, 40),
    summary,
    data,
  };
}

/** Apply one ci-report to a ledger. */
export function applyReport(ledger, report, now = new Date().toISOString()) {
  const next = ledger || emptyLedger(report.repository);
  const run = runRecord(next, report.workflow, report.run_id, now);
  run.sha ||= report.sha;
  run.event ||= report.event;
  run.branch ||= report.ref.replace(/^refs\/(heads|tags)\//, "");
  run.reports[report.job] = {
    status: report.status || null,
    summary: report.summary,
    data: report.data,
    run_attempt: report.run_attempt,
    reported_at: now,
  };
  run.updated_at = now;
  next.updated_at = now;
  return next;
}

/**
 * Read-modify-write `repositories/<id>.json` on the ci-status branch, retrying on concurrent writes
 * (one CI run emits many job events). `api(path, method, body)` is the Worker's GitHub client and
 * throws an Error whose message carries the status code. Creates the orphan branch when missing.
 */
export async function updateLedger(api, centralRepository, repositoryId, mutate) {
  const filePath = `repositories/${Number(repositoryId)}.json`;
  const contentsPath = `/repos/${centralRepository}/contents/${filePath}`;
  for (let attempt = 1; attempt <= MAX_WRITE_ATTEMPTS; attempt += 1) {
    let current = null;
    let sha;
    try {
      const file = await api(`${contentsPath}?ref=${CI_STATUS_BRANCH}`, "GET");
      sha = file.sha;
      current = JSON.parse(decodeBase64Utf8(file.content || ""));
    } catch (error) {
      if (!/\(404\)/.test(String(error.message))) throw error;
      await ensureBranch(api, centralRepository);
    }
    const next = mutate(current);
    try {
      await api(contentsPath, "PUT", {
        message: `ci-status: ${next.repository.full_name}`,
        content: encodeBase64Utf8(JSON.stringify(next, null, 2) + "\n"),
        branch: CI_STATUS_BRANCH,
        ...(sha ? { sha } : {}),
      });
      return next;
    } catch (error) {
      // 409 / 422: someone else wrote first. Re-read and re-apply.
      if (!/\((409|422)\)/.test(String(error.message)) || attempt === MAX_WRITE_ATTEMPTS) throw error;
      await new Promise((resolve) => setTimeout(resolve, 150 * attempt + Math.floor(Math.random() * 200)));
    }
  }
  throw new Error("ci-status write did not converge");
}

async function ensureBranch(api, centralRepository) {
  try {
    await api(`/repos/${centralRepository}/git/ref/heads/${CI_STATUS_BRANCH}`, "GET");
    return;
  } catch (error) {
    if (!/\(404\)/.test(String(error.message))) throw error;
  }
  const readme = "# CI status\n\nRendered by `.github/workflows/ci-status-dashboard.yml` on `main`.\n";
  const blob = await api(`/repos/${centralRepository}/git/blobs`, "POST", { content: readme, encoding: "utf-8" });
  const tree = await api(`/repos/${centralRepository}/git/trees`, "POST", {
    tree: [{ path: "README.md", mode: "100644", type: "blob", sha: blob.sha }],
  });
  const commit = await api(`/repos/${centralRepository}/git/commits`, "POST", {
    message: "ci-status: initialize ledger branch",
    tree: tree.sha,
    parents: [],
  });
  try {
    await api(`/repos/${centralRepository}/git/refs`, "POST", {
      ref: `refs/heads/${CI_STATUS_BRANCH}`,
      sha: commit.sha,
    });
  } catch (error) {
    // Another delivery created it first.
    if (!/\(422\)/.test(String(error.message))) throw error;
  }
}

function encodeBase64Utf8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

function decodeBase64Utf8(value) {
  const binary = atob(String(value).replace(/\s+/g, ""));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

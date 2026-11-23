/**
 * Cancel only older duplicates, using immediately issued GitHub force-cancel requests.
 * Missing timing, history, or reliable identity never authorizes killing running work.
 */
const PENDING = new Set(["queued", "pending", "waiting", "requested"]);
const CENTRAL = "hereliesaz/workflows";
const INTERNAL = new Set([
  ".github/workflows/cancel-runs.yml",
  ".github/workflows/ci-status-dashboard.yml",
  ".github/workflows/sync-all-repositories.yml",
  ".github/workflows/sync-registry-changes.yml",
  ".github/workflows/sync-repository.yml",
  ".github/workflows/validate-controller.yml",
  ".github/workflows/version-contract-sync.yml",
]);

export function duplicateIdentity(repository, run, registered = []) {
  const id = Number(run?.workflow_id);
  if (!Number.isSafeInteger(id) || id <= 0 || !repository?.full_name ||
      !Number.isSafeInteger(Number(repository.id))) return null;
  if (String(repository.full_name).toLowerCase() !== CENTRAL) {
    return `${repository.id}:${id}`;
  }
  const path = String(run.path || "");
  // The gateway carries distinct events. Dropping a queued event loses its dispatch.
  if (path.endsWith("/gateway.yml")) return null;
  if (INTERNAL.has(path)) return `${repository.id}:${id}`;

  const title = String(run.display_title || "").trim();
  const web = /^Web Deploy · repository ([0-9]+)$/.exec(title);
  if (web) return `${web[1]}:${id}:web-deploy`;

  const parts = /^([A-Za-z0-9_.-]+) · (.+)$/.exec(title);
  if (!parts) return null;
  const match = registered.find((entry) =>
    String(entry?.repository || "").toLowerCase() ===
      `hereliesaz/${parts[1].toLowerCase()}`);
  if (!match) return null;
  const action = parts[2].replace(/ · [0-9a-f]{7,40}$/i, "").trim().toLowerCase();
  return action ? `${match.id}:${id}:${action}` : null;
}

export function historicalAverageMs(runs) {
  const durations = [];
  for (const run of runs) {
    if (run.status !== "completed" || run.conclusion !== "success") continue;
    const start = Date.parse(run.run_started_at || "");
    const end = Date.parse(run.updated_at || "");
    const ms = end - start;
    if (!Number.isFinite(ms) || ms <= 0 || ms > 24 * 3600_000) continue;
    durations.push(ms);
    if (durations.length === 5) break;
  }
  if (durations.length < 3) return null;
  return durations.reduce((sum, ms) => sum + ms, 0) / durations.length;
}

/** api(path, method?, body?, allowEmpty?) is the verified GitHub App API. */
export async function cancelOlderDuplicates(repository, current, api, registered, now = Date.now()) {
  const currentId = Number(current?.id);
  const identity = duplicateIdentity(repository, current, registered);
  if (!identity || !Number.isSafeInteger(currentId) || currentId <= 0) {
    return { cancelled: [], skipped: "unidentified" };
  }
  const base = `/repos/${repository.full_name}/actions`;
  const history = await api(`${base}/workflows/${current.workflow_id}/runs?per_page=100`);
  if (!Array.isArray(history?.workflow_runs)) {
    return { cancelled: [], skipped: "history-unavailable" };
  }
  const older = history.workflow_runs.filter((run) =>
    Number.isSafeInteger(Number(run.id)) &&
    Number(run.id) < currentId &&
    duplicateIdentity(repository, run, registered) === identity
  ).sort((a, b) => Number(b.id) - Number(a.id));
  const average = historicalAverageMs(older);
  const cancelled = [];
  const failures = [];
  for (const run of older) {
    let reason;
    if (PENDING.has(run.status)) {
      reason = "pending";
    } else if (run.status === "in_progress" && average !== null && Number.isFinite(now)) {
      const started = Date.parse(run.run_started_at || "");
      const elapsed = now - started;
      if (Number.isFinite(started) && elapsed >= 0 && elapsed * 2 < average) {
        reason = "under-halfway";
      }
    }
    if (!reason) continue;
    try {
      // Do not try the slow /cancel path first, and never sleep before this call.
      await api(`${base}/runs/${run.id}/force-cancel`, "POST", undefined, true);
      cancelled.push({ id: Number(run.id), reason });
    } catch (error) {
      // A cancellation failure must never prevent processing the incoming event.
      failures.push({ id: Number(run.id), reason: String(error?.message || error) });
    }
  }
  return { cancelled, failures, average_ms: average };
}

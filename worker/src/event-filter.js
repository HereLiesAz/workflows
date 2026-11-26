import { EVENT_CONSUMERS } from "./event-consumers.js";

/**
 * Decide whether a verified repository webhook can start a gateway run.
 *
 * Returns null when some active registered workflow of that repository consumes the event
 * (the gateway then makes the exact branch/path/action routing decision, unchanged), or the
 * reason the event is dropped. `consumers` defaults to the map generated from the registry by
 * scripts/generate_event_consumers.py.
 */
export function webhookDropReason(repositoryId, eventName, consumers = EVENT_CONSUMERS) {
  const entry = Object.prototype.hasOwnProperty.call(consumers, String(repositoryId))
    ? consumers[String(repositoryId)]
    : undefined;
  if (!entry) return "Repository is not registered with the central controller";
  if (!entry.events.includes(eventName)) {
    return "No active registered workflow of this repository consumes this event";
  }
  return null;
}

const CI_SKIP_TOKENS = ["[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]"];

function hasSkipToken(message) {
  const text = String(message || "").toLowerCase();
  return CI_SKIP_TOKENS.some((token) => text.includes(token));
}

/**
 * Drop push deliveries the gateway would route to nothing, before they cost a queued gateway run.
 *
 * Every gateway run competes for the account's concurrent-job limit with real builds, so a push
 * that can never start a workflow only delays the ones that can (2026-09-29: Graffux release
 * pushes waited 85 minutes in that queue and their trackers gave up). Mirrors
 * scripts/dispatch_request.py, which already ignores these after the run has started:
 * - branch/tag deletions (GitHub never runs push workflows for them; nothing is to be synced);
 * - pushes whose head commit, or every commit, carries a CI-skip token (the controller's own
 *   "chore(version): … [skip ci]" commits land here after every release).
 * Returns null to forward, or the reason for dropping.
 */
export function pushDropReason(event) {
  if (!event || typeof event !== "object") return null;
  if (event.deleted === true) return "Push deletes a ref; no workflow runs for it";
  const head = event.head_commit && typeof event.head_commit === "object" ? event.head_commit : null;
  const commits = Array.isArray(event.commits)
    ? event.commits.filter((commit) => commit && typeof commit === "object")
    : [];
  if ((head && hasSkipToken(head.message)) ||
      (commits.length > 0 && commits.every((commit) => hasSkipToken(commit.message)))) {
    return "Push carries an explicit CI-skip token";
  }
  return null;
}

// A conservative subset of Python fnmatch: only literals and '*' are evaluated here.
// Anything more complex is unknown, and unknown never causes an event to be dropped.
function matchPattern(value, pattern) {
  if (typeof pattern !== "string" || /[?\[\]\\]/.test(pattern)) return null;
  const pieces = pattern.split("*");
  if (pieces.length === 1) return value === pattern;
  if (!value.startsWith(pieces[0]) || !value.endsWith(pieces.at(-1))) return false;
  let offset = pieces[0].length;
  const end = value.length - pieces.at(-1).length;
  if (offset > end) return false;
  for (const piece of pieces.slice(1, -1)) {
    const next = value.indexOf(piece, offset);
    if (next < 0 || next + piece.length > end) return false;
    offset = next + piece.length;
  }
  return true;
}

function orderedMayMatch(value, patterns = []) {
  if (patterns.some(pattern => typeof pattern !== "string" || pattern.startsWith("!"))) return true;
  const positive = patterns.filter(Boolean);
  return !positive.length || positive.some(pattern => matchPattern(value, pattern) !== false);
}

function definitelyIgnored(value, patterns = []) {
  return patterns.some(pattern => pattern && matchPattern(value, pattern) === true);
}

function completePushFiles(event) {
  // A truncated or incomplete delivery must still reach the authoritative dispatcher.
  if (!Array.isArray(event.commits) || !Number.isInteger(event.size) ||
      event.size !== event.commits.length || event.size === 0) return null;
  const files = new Set();
  for (const commit of [...event.commits, event.head_commit]) {
    if (!commit || !["added", "modified", "removed"].every(key =>
      Array.isArray(commit[key]) && commit[key].every(path => typeof path === "string"))) return null;
    for (const key of ["added", "modified", "removed"]) for (const path of commit[key]) files.add(path);
  }
  return [...files];
}

function ruleMayMatch(rule, eventName, event, files) {
  if (event.action && rule.types?.length && !rule.types.includes(event.action)) return false;
  if (eventName === "push") {
    if (typeof event.ref !== "string") return true;
    const tag = event.ref.startsWith("refs/tags/");
    if (!tag && !event.ref.startsWith("refs/heads/")) return true;
    // Match the dispatcher’s one replacement of each prefix, even for unusual nested ref names.
    const ref = event.ref.replace("refs/heads/", "").replace("refs/tags/", "");
    const include = rule[tag ? "tags" : "branches"] || [];
    const other = rule[tag ? "branches" : "tags"] || [];
    if (other.length && !include.length) return false;
    if (!orderedMayMatch(ref, include) || definitelyIgnored(ref, rule[tag ? "tags-ignore" : "branches-ignore"])) return false;
  }
  if (eventName === "pull_request") {
    const base = event.pull_request?.base?.ref;
    if (typeof base === "string" && (!orderedMayMatch(base, rule.branches) || definitelyIgnored(base, rule["branches-ignore"]))) return false;
  }
  if (files !== null) {
    if (rule.paths?.length && !files.some(path => orderedMayMatch(path, rule.paths))) return false;
    if (files.length && rule["paths-ignore"]?.length && files.every(path => definitelyIgnored(path, rule["paths-ignore"]))) return false;
  }
  return true;
}

/**
 * Drop only events provably unmatched by every active registry trigger. Missing metadata,
 * complex patterns and unavailable PR changed-file lists deliberately reach the gateway.
 * Default-branch pushes that may change workflow setup must also reach repository sync.
 */
export function routingDropReason(repositoryId, eventName, event, consumers = EVENT_CONSUMERS) {
  const entry = consumers[String(repositoryId)];
  if (!entry?.routing || !event || typeof event !== "object") return null;
  const rules = entry.routing[eventName] || [];
  const files = eventName === "push" ? completePushFiles(event) : null;
  if (eventName === "push") {
    const defaultBranch = event.repository?.default_branch;
    if (!defaultBranch || typeof event.ref !== "string" ||
        (entry.default_branch && entry.default_branch !== defaultBranch)) return null;
    if (event.ref === `refs/heads/${defaultBranch}` &&
        (files === null || files.some(path => path.startsWith(".github/workflows/") || path === ".github/workflow-request.yml"))) return null;
  }
  return rules.some(rule => ruleMayMatch(rule, eventName, event, files))
    ? null : "No active workflow matches the delivered action, ref or known changed paths";
}

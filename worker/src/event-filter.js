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

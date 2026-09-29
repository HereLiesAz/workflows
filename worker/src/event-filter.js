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

// Best-effort webhook delivery de-duplication on the Workers Cache API.
//
// The Worker has no durable storage binding, so this is per data center and expires after an hour:
// it stops the common replay (GitHub or a proxy redelivering the same X-GitHub-Delivery, or a
// captured signed body replayed soon after) without claiming exactly-once delivery. Where `caches`
// does not exist (tests, other runtimes) nothing is deduplicated.

const TTL_SECONDS = 3600;

function keyFor(delivery) {
  return new Request(`https://webhook-dedupe.invalid/${encodeURIComponent(String(delivery))}`);
}

function cache() {
  try {
    return typeof caches !== "undefined" ? caches.default : null;
  } catch {
    return null;
  }
}

export async function isDuplicateDelivery(delivery) {
  const store = cache();
  if (!store) return false;
  try {
    return Boolean(await store.match(keyFor(delivery)));
  } catch {
    return false;
  }
}

export async function markDelivery(delivery) {
  const store = cache();
  if (!store) return;
  try {
    await store.put(keyFor(delivery), new Response("1", { headers: { "Cache-Control": `max-age=${TTL_SECONDS}` } }));
  } catch {
    // Dedupe is an optimization; never fail a handled delivery over it.
  }
}

/**
 * Best-effort "first time we have seen this key" check backed by an optional
 * Workers KV binding.
 *
 * KV has no compare-and-swap, so two simultaneous requests can both win; this
 * stops replays and floods, not races. With no binding (the default) every call
 * is the first: behaviour is unchanged until a namespace is bound to
 * WEBHOOK_SEEN in wrangler.jsonc.
 *
 * Fails open on a KV error: refusing legitimate GitHub deliveries because the
 * dedupe store hiccuped would be worse than the replay it guards against.
 */
export async function claimOnce(kv, key, ttlSeconds) {
  if (!kv || typeof kv.get !== "function") return true;
  try {
    if (await kv.get(key) !== null) return false;
    await kv.put(key, "1", { expirationTtl: Math.max(60, Math.floor(ttlSeconds)) });
    return true;
  } catch {
    return true;
  }
}

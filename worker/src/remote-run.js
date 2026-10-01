const PURPOSE = "HereLiesAz/workflows:remote-run-callback:v1";

export async function createRemoteRunToken(secret, claims) {
  if (!secret) throw new Error("Remote-run signing secret is required");
  const payload = {
    v: 1,
    ...claims,
  };
  const encoded = base64UrlEncodeUtf8(JSON.stringify(payload));
  const signature = await sign(secret, encoded);
  return `${encoded}.${base64UrlEncodeBytes(signature)}`;
}

export async function verifyRemoteRunToken(secret, token, now = Math.floor(Date.now() / 1000)) {
  if (!secret) throw new Error("Remote-run signing secret is required");
  const [encoded, signatureText, extra] = String(token || "").split(".");
  if (!encoded || !signatureText || extra !== undefined) throw new Error("Malformed remote-run token");

  const valid = await verify(secret, encoded, base64UrlDecode(signatureText));
  if (!valid) throw new Error("Invalid remote-run token");

  let payload;
  try {
    payload = JSON.parse(new TextDecoder().decode(base64UrlDecode(encoded)));
  } catch {
    throw new Error("Malformed remote-run payload");
  }

  if (payload.v !== 1) throw new Error("Unsupported remote-run token version");
  if (!Number.isFinite(payload.iat) || !Number.isFinite(payload.exp)) throw new Error("Remote-run token has invalid timestamps");
  if (payload.iat > now + 60) throw new Error("Remote-run token is not valid yet");
  if (payload.exp < now) throw new Error("Remote-run token has expired");
  return payload;
}

export function normalizeRemoteRunState(value) {
  const state = String(value || "").toLowerCase();
  if (state === "success" || state === "completed" || state === "complete") return "success";
  if (["failure", "failed", "error", "cancelled", "canceled"].includes(state)) return "failure";
  throw new Error("Remote-run state must be success or failure");
}

export function sanitizeStatusDescription(value, fallback) {
  const text = String(value || fallback || "").replace(/\s+/g, " ").trim();
  return text.slice(0, 140) || String(fallback || "Remote run finished.").slice(0, 140);
}

async function sign(secret, payload) {
  const key = await importKey(secret, ["sign"]);
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(`${PURPOSE}:${payload}`),
  );
  return new Uint8Array(signature);
}

async function verify(secret, payload, signature) {
  const key = await importKey(secret, ["verify"]);
  return crypto.subtle.verify(
    "HMAC",
    key,
    signature,
    new TextEncoder().encode(`${PURPOSE}:${payload}`),
  );
}

async function importKey(secret, usages) {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(String(secret)),
    { name: "HMAC", hash: "SHA-256" },
    false,
    usages,
  );
}

function base64UrlEncodeUtf8(value) {
  return base64UrlEncodeBytes(new TextEncoder().encode(value));
}

function base64UrlEncodeBytes(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlDecode(value) {
  const normalized = String(value).replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

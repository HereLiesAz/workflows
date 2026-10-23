# Worker security notes

## Remote-run callback tokens

`/remote-run/start` issues an HMAC token that remote compute (for example Kaggle) presents once to
`/remote-run/callback` when it finishes. Tokens default to 4 hours and are capped at 8 hours
(`callback_ttl_seconds` in a purpose profile; larger requests are clamped). Each token carries a
random `jti`.

The Worker has **no storage binding**, so it cannot by itself make a token single-use. To enable
that, an owner must create a Workers KV namespace and bind it as `REMOTE_RUN_JTI` in the Worker's
configuration; the callback then consumes each `jti` once and answers `409` on replay. KV is
eventually consistent, so this narrows replay rather than making it atomic. Until it is bound, the
short TTL is the only bound on replay.

## Webhook de-duplication

With a `WEBHOOK_SEEN` KV namespace bound, `/webhook` accepts a given signed body once per day. The
key is the SHA-256 of the body, not the `X-GitHub-Delivery` header, which the signature does not cover.
KV has no compare-and-swap, so this stops replays and floods, not races, and a body is claimed before it
is dispatched. Without the binding nothing is deduplicated.

The remote-run callback token is single-use when `REMOTE_RUN_JTI` is bound: it is checked first and
recorded only after the finalizer dispatch succeeded, so a malformed or failed first attempt does not
burn it.

## Error bodies

GitHub API failures are written to the Worker log; callers see only `GitHub API failed (<status>)`.

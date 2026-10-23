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

`/webhook` skips a repeated `X-GitHub-Delivery` id using the Workers Cache API. It is per data
center and lasts an hour, a best-effort guard rather than exactly-once delivery. A delivery is
marked only after it was handled.

## Error bodies

GitHub API failures are written to the Worker log; callers see only `GitHub API failed (<status>)`.

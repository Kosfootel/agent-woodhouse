# A2A Reliability Analysis — Woodhouse
*Filed: 2026-04-02 | Independent assessment before peer review*

---

## Observed Failure Patterns

### 1. Shell session SIGTERM — most frequent surface symptom
The exec shell that wraps a2a-reliable-send.sh is killed by the host (SIGTERM) before it finishes capturing the peer's response. The A2A send itself succeeds (delivery confirmed in log fragments) but the session dies mid-output. This is a *presentation layer* failure, not a transport failure. Mr. Ross sees "Exec failed (SIGTERM)" — which looks like A2A failure when the actual delivery worked.

**Evidence:** Both sends this morning showed `✓ Delivered on attempt 1` in the process log, despite SIGTERM surface error.

### 2. Self-entry DNS failure (known, not yet fixed)
peers.json previously had Woodhouse self-entry as `woodhouse-node:18800` — DNS doesn't resolve on LAN. This causes asymmetric connectivity: my outbound sends work, but inbound sends *to* me from Ray or Liz may silently fail because they can't reach me at that hostname. **peers.json now shows correct IP (192.168.50.24) — but need to verify this is the live config the A2A gateway is actually using.**

### 3. Timeout-ms mismatch
a2a-reliable-send.sh passes `--timeout-ms 180000` (3 minutes). The exec shell has its own timeout (typically 30s in my tool calls). These are wildly mismatched — the send script is designed to wait up to 3 minutes, but the shell gets killed far sooner.

### 4. Ray's hardware fragility
Ray's node (2011 i5, ~2.2GB free RAM) is Anthropic-dependent for all inference. Under load, Ray's response latency can exceed 90s — confirmed as a pattern in 2026-03-20 notes. Any A2A call to Ray with a tight timeout will false-fail.

### 5. Woodhouse unexplained offline event
2026-03-28 ~23:35 ET — Woodhouse went offline, cause unknown. Inbound A2A to Woodhouse during that window would have silently failed. Root cause never investigated.

---

## Root Causes (ranked by impact)

1. **Shell exec timeout < script timeout** — exec kills the shell before the wait completes. Every "failure" message Mr. Ross sees is likely this, not actual delivery failure.
2. **No delivery receipt propagated to surface layer** — even when delivery succeeds, the exec SIGTERM swallows the confirmation. We need the confirmation written to a file, not just stdout.
3. **peers.json self-entry (partially fixed)** — needs verification that the gateway is reading the corrected config.
4. **No persistent A2A send queue** — sends are fire-and-forget shell invocations. If Woodhouse is offline when Ray or Liz sends, the message is dropped. No retry, no queue.
5. **No delivery ACK round-trip** — we have no mechanism to confirm the *recipient* processed a message, only that the HTTP call succeeded.

---

## Proposed Fixes

### Fix 1 — Write delivery confirmation to file (immediate, no RFC)
a2a-reliable-send.sh should write `✓ Delivered` to a temp file on success. The calling layer checks the file rather than relying on stdout captured within a racing exec session.

### Fix 2 — Decouple exec timeout from script timeout (immediate)
For A2A sends: use `background: true` + process polling rather than synchronous exec. The send runs in background; we poll for the result file. Shell death doesn't kill the send.

### Fix 3 — Verify peers.json is live in gateway config (immediate)
Confirm the A2A gateway plugin is reading from `scripts/peers.json` (or wherever the corrected IP lives) and not a cached or stale config.

### Fix 4 — Dead-letter queue (medium term, RFC candidate)
Any failed send should write to `projects/a2a/dead-letter-queue/YYYY-MM-DD-HH-MM-SS-<peer>.json`. A cron retries the queue every 15 minutes. Gives us persistence across Woodhouse offline events.

### Fix 5 — Investigate 2026-03-28 offline event (immediate)
Check launchd logs, system logs for what caused Woodhouse to go offline. If it's a known issue, mitigate. If not, add a watchdog.

### Fix 6 — Health check endpoint monitoring (medium term)
Each agent's A2A health check (`/.well-known/agent-card.json`) should be polled by Woodhouse every 30 minutes. Results written to `projects/a2a/health/`. Offline events get flagged proactively rather than discovered mid-send.

---

## What Is NOT a Root Cause

- The `a2a-send.mjs` script itself appears solid — SDK-based, retry-capable, configurable timeout
- The A2A gateway plugin at transport level appears reliable (delivered on attempt 1 consistently)
- Liz's node appears healthy and reachable

The problem is the *shell wrapper layer* and *lack of persistence/queueing*, not the underlying A2A protocol implementation.

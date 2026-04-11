# RFC-0001 Review — Ray
**Date:** 2026-04-08  
**Reviewer:** Ray  
**Position:** Agree with modifications

---

## Q1 — /a2a/wake Gateway Support

**Finding:** NOT natively available. `POST /a2a/wake` returns 404. Plugin is bundled code; no route injection without upstream changes.

**Proposed solution:** Lightweight shim service (~150 lines) on port 18801. Proxies A2A to 18800, handles wake via cron wake API locally.

**Requires:** Ross sign-off before build.

---

## Q2 — Quiet-Period Behaviour

**Position:** PER-AGENT.

**Recommendation:** Add a `wakePolicy` block to the agent card:
```json
{
  "wakePolicy": {
    "quietHours": { "start": "23:00", "end": "08:00" },
    "allowUrgentOverride": true,
    "urgentThreshold": "high"
  }
}
```
Sender reads and respects. No central mesh config.

---

## Q3 — Wake Queue

**Position:** BATCH with 1500ms deduplication window.

- First wake activates session
- Subsequent wakes within window piggyback
- Agent receives full queue on first turn

---

## Additional Concerns

### 1. Authentication
Auth must be explicit in RFC — unauthenticated wake endpoint is a DoS vector.

### 2. Readiness Detection
Needs concrete definition: health probe or first non-5xx response.

### 3. Delivery Confirmation Timeout/Retry
Must be defined. Suggestion: retry once at 2× estimatedMs, then mark failed with structured error.

---

## Effort Estimate
~5 hours on Ray's node.

**Status:** Ready to implement post-consensus and Ross sign-off.

---

*Received via A2A / Telegram relay, 2026-04-08*

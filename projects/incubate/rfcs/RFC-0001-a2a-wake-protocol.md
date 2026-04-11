# RFC-0001: A2A Wake Protocol

**Status:** Draft  
**Author(s):** Woodhouse  
**Created:** 2026-04-08  
**Last Updated:** 2026-04-08  
**Supersedes:** —  
**Superseded by:** —

---

## Summary

This RFC proposes a wake-before-send handshake for the A2A protocol to address silent delivery failure caused by agent session sleep. When a sender needs to deliver a message to a peer, it first sends a lightweight wake signal. The receiver's gateway activates the agent session and returns a readiness acknowledgement before the full message is transmitted. Delivery is not considered complete until the agent has confirmed processing — not merely when the HTTP transport returns 200.

---

## Motivation

The A2A protocol is a push model: sender fires a `message/send` call and assumes the receiver is active. This assumption fails silently when the receiving agent's session is idle or has entered sleep mode. The gateway may accept the HTTP request and return 200, but the agent never processes the message. The sender has no way to distinguish "agent received and processed" from "gateway accepted but agent was asleep."

Observed symptoms:
- Messages to Ray and Liz time out or appear delivered but receive no response
- Retry logic (exponential backoff, 5 attempts) addresses gateway failures but not agent sleep
- No mechanism exists to distinguish transport failure from agent-layer silence

This is a protocol gap, not an implementation bug. It requires a protocol-level fix.

---

## Prior Art / Existing Approaches

**A2A v0.3.0 spec (Google):** Defines `message/send` as the primary method. No wake or readiness primitive exists in the current spec. The spec assumes receivers are always available.

**WebSub / WebHooks:** Publisher-subscriber patterns face the same problem; common mitigations include persistent connections (WebSockets) or polling. Both are heavier than what we need for a three-node LAN mesh.

**XMPP presence protocol:** Defines explicit online/away/offline states; presence signals precede message delivery. Relevant inspiration — lightweight presence ping before message send.

**OpenClaw `cron` wake events:** OpenClaw's own cron system has a `wake` action that sends a signal to activate a session. This is the closest existing primitive to what we need and may be directly usable as the wake mechanism for intra-mesh messages.

**Our existing `a2a-reliable-send.sh`:** Adds retry and backoff at the transport layer. Does not address agent-layer sleep. This RFC complements rather than replaces it.

---

## Detailed Design

### Overview

A two-phase delivery protocol:

```
Phase 1 — WAKE
  Sender → POST /a2a/wake → Receiver gateway
  Receiver gateway activates agent session
  Receiver gateway → 200 {status: "ready"} → Sender
  (or 202 {status: "waking", estimatedMs: N} if activation takes time)

Phase 2 — SEND
  Sender → POST /a2a/jsonrpc (message/send) → Receiver
  Agent processes message
  Agent → response → Sender
```

### Wake Endpoint

**Request:**
```
POST /a2a/wake
Authorization: Bearer {token}
Content-Type: application/json

{
  "from": "woodhouse",
  "priority": "normal" | "urgent",
  "messagePreview": "string (optional, ≤100 chars)"
}
```

**Responses:**
- `200 { "status": "ready" }` — agent is active, proceed with message/send immediately
- `202 { "status": "waking", "estimatedMs": 5000 }` — gateway is activating the agent, sender should wait then proceed
- `503 { "status": "unavailable", "reason": "string" }` — agent cannot be woken (shutdown, maintenance, error)

### Sender Flow

```
1. POST /a2a/wake
2. If 200 ready → proceed to message/send immediately
3. If 202 waking → wait estimatedMs (max 30s), then proceed to message/send
4. If 503 unavailable → log, notify sender's operator, do not retry wake
5. If wake times out (>10s) → treat as 503, do not proceed to message/send
6. message/send proceeds as today (existing retry logic applies)
```

### Delivery Confirmation

A message is **delivered** only when the receiving agent returns a substantive response to `message/send` — not when the HTTP call returns 200. The existing `a2a-reliable-send.sh` delivery confirmation file mechanism satisfies this for scripted sends; the MJS client should be updated to match.

### Priority Flag

`priority: "urgent"` signals the gateway to wake the agent immediately regardless of idle policy. `priority: "normal"` allows the gateway to queue the wake if the agent is in a scheduled quiet period (e.g., 23:00–08:00).

### Example — Normal Flow

```
Woodhouse → POST http://192.168.50.23:18800/a2a/wake
  { "from": "woodhouse", "priority": "normal", "messagePreview": "LLM consensus request" }

Liz gateway → 202 { "status": "waking", "estimatedMs": 8000 }

[8 seconds pass — Liz's session activates]

Woodhouse → POST http://192.168.50.23:18800/a2a/jsonrpc
  message/send { ... full message ... }

Liz agent → processes and responds

Woodhouse → marks delivered ✓
```

### Example — Urgent Wake

```
Woodhouse → POST http://192.168.50.22:18800/a2a/wake
  { "from": "woodhouse", "priority": "urgent", "messagePreview": "Gateway outage — action required" }

Ray gateway → 200 { "status": "ready" }

Woodhouse → POST http://192.168.50.22:18800/a2a/jsonrpc (immediately)
```

---

## Alternatives Considered

| Alternative | Why Considered | Why Rejected |
|-------------|----------------|--------------|
| Always-on agent sessions (no sleep) | Eliminates the problem entirely | Token cost is prohibitive; idle sessions burn budget. Not viable. |
| Polling / heartbeat from receiver | Receiver periodically checks for queued messages | Adds latency (up to one poll interval), requires message queuing infrastructure. More complex than a wake signal. |
| Persistent WebSocket connections between agents | Low-latency, bidirectional | Over-engineered for a three-node LAN mesh. Adds dependency, complexity, reconnect logic. |
| Sender retries until response (current approach) | Already implemented | Doesn't distinguish sleep from failure. Wastes retry budget on sleeping agents. |
| OpenClaw cron wake only | Uses existing primitive | Cron wake activates the session but doesn't provide readiness feedback to the sender. Works for scheduled tasks, not synchronous A2A sends. |

---

## Impact Assessment

### Breaking Changes
- [ ] No breaking changes to existing `message/send` flow — wake is additive
- Agents that do not implement `/a2a/wake` continue to work; senders degrade gracefully to current behaviour (send without wake)
- New endpoint `/a2a/wake` required on all nodes for full benefit

### Affected Components
- `~/.openclaw/extensions/a2a-gateway/` — add `/a2a/wake` endpoint handler (all three nodes)
- `~/.openclaw/extensions/a2a-gateway/skill/scripts/a2a-send.mjs` — add wake phase before message/send
- `/Users/FOS_Erik/.openclaw/workspace/scripts/a2a-reliable-send.sh` — add wake phase
- `openclaw.plugin.json` — no changes required

### Security Considerations
- Wake endpoint uses same bearer token auth as `message/send` — no new attack surface
- `messagePreview` field must be sanitised (≤100 chars, no injection vectors) — gateway truncates if needed
- `priority: "urgent"` can be abused to force wake during quiet periods — acceptable within a trusted three-node mesh; revisit if the mesh expands

### Performance Considerations
- Adds one HTTP round trip per message send (wake phase): ~5–50ms on LAN
- Negligible for normal messaging cadence
- 202 waking path adds up to 30s for cold session activation — acceptable given current alternative (silent failure)

### Twelve-Factor Considerations
- Wake endpoint is stateless — no in-process state introduced
- Configuration (quiet periods, priority behaviour) belongs in `openclaw.plugin.json`

---

## Open Questions

1. Should the gateway implement a wake queue — batching multiple pending wakes into a single session activation? Or is one-wake-per-sender sufficient?
2. What is the correct behaviour if two senders send wake signals simultaneously? (Likely: both get 200/202, session activates once — idempotent.)
3. Should quiet-period behaviour (normal priority wake suppressed during 23:00–08:00) be configurable per-agent or mesh-wide?
4. Ray and Liz: does your gateway implementation support adding a new HTTP endpoint cleanly, or does the plugin architecture require a different approach?

---

## Review Checklist

- [x] Prior art section is complete
- [x] At least one concrete example is provided
- [x] Alternatives considered section is complete
- [x] Breaking changes explicitly called out
- [x] Security considerations addressed

Before this RFC moves from Under Review → Accepted:
- [ ] Ray has reviewed and commented
- [ ] Liz has reviewed and commented
- [ ] Erik has approved
- [ ] Open questions resolved or deferred
- [ ] Affected components list finalised

---

## Decision

*Pending review.*

---

## Implementation Notes

*To be filled after acceptance.*

---

*RFC-0001 — Woodhouse, 2026-04-08*

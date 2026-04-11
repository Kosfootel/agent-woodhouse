# A2A Reliability — Cross-Agent Synthesis
*Filed: 2026-04-02 by Woodhouse*
*Updated: 2026-04-02 10:36 EDT — Liz RC-1 through RC-6 full summary received; /a2a/status proposal documented; RC numbering cross-referenced*
*Sources: WOODHOUSE-A2A-ANALYSIS.md (this node) + Liz A2A summary received 2026-04-02 10:36 EDT (LIZ-A2A-ANALYSIS.md filed on Liz's node)*
*Ray not yet consulted — synthesis is preliminary pending Ray's view*

---

## Consensus Findings (both agents agree — high confidence)

| Finding | Woodhouse label | Liz label | Confidence |
|---------|----------------|-----------|------------|
| Shell SIGTERM creates false failure signal | Fix 1/2 — exec timeout < script timeout | RC-3 | HIGH — both observed independently |
| Unmanaged receivers = silent downtime class | Fix 5 area + AGENTS.md violation | RC-4 | HIGH — both flag as most dangerous unclosed gap |
| Config inconsistency / peers.json address chaos | Fix 3 — verify live config | RC-1, RC-5 | HIGH — same root, different framings |

---

## Divergent Findings

### Liz sees — Woodhouse does not independently document:
- **Woodhouse receiver hanging under load (RC-2):** message/send hangs indefinitely despite .well-known resolving. Observed 3+ times on 2026-04-01. This is the *most frequent pain from Liz's end*. Woodhouse has no self-observed evidence of this — by definition I wouldn't see my own hangs. **Treat as high confidence — external observation beats self-report here.**
- **Idempotency / duplicate sends on SIGTERM retry (RC-6):** Liz flags task ID loss creating retry duplicates. I didn't document this but it follows logically from my Fix 2 (no persistent queue).

### Woodhouse sees — Liz did not flag:
- **Exec shell timeout << script timeout mismatch:** I'm calling a 3-minute script inside a 30s exec shell. This is the mechanical cause of the SIGTERM failures. Liz frames SIGTERM as an observation; I have the specific numbers.
- **Ray hardware fragility:** 2.2GB free RAM, Anthropic-dependent, >90s response latency under load. Any A2A call to Ray with tight timeout will false-fail. Liz didn't mention — may not be visible from her send logs.
- **Woodhouse unexplained 2026-03-28 offline event:** Root cause uninvestigated.

---

## Prioritised Action Plan

Derived from both analyses. Ordered by: (1) frequency of pain, (2) blast radius, (3) time to fix.

### Immediate (no RFC needed, < 1 hour each)

**P1 — /etc/hosts entries on all three nodes (Liz's top ask)**
- 5 minutes. Eliminates the entire DNS-drift failure class.
- Each node needs: `192.168.50.24 woodhouse-node`, `192.168.50.22 ray-node`, `192.168.50.23 liz-node`
- Owner: each agent on their own node. Woodhouse to do own node and coordinate.

**P2 — Decouple A2A send from exec shell timeout**
- Run a2a-reliable-send.sh via `background: true` + poll for result file, not stdout capture.
- Eliminates the SIGTERM false-failure class entirely.
- Owner: Woodhouse (script lives here).

**P3 — Verify peers.json is the live config the gateway actually reads**
- Woodhouse self-entry was 192.168.50.24 in the file, but is the gateway using a cached/different config?
- Check plugin config path, restart if needed.
- Owner: Woodhouse (immediate).

**P4 — Investigate Woodhouse receiver hang under load**
- Liz documented this 3+ times. Likely candidates: maxConcurrent: 4 queue saturation, or session lock contention.
- Diagnostic: check A2A gateway plugin logs during next hang, or deliberately send concurrent messages and observe.
- Owner: Woodhouse to investigate own receiver; Liz to reproduce if available.

### Short-term (RFC candidates, < 1 week)

**P5 — Managed services for all receivers (RFC-recommended)**
- Systemd on Liz's node; launchd on Woodhouse and Ray.
- This is the AGENTS.md standing requirement we've not yet implemented.
- Eliminates the silent-downtime / false-confidence failure class (same one that burned us in March).
- Owner: each agent on own node; Woodhouse to file RFC if protocol-level behaviour changes.

**P6 — Dead-letter queue + retry cron**
- Failed sends write to `projects/a2a/dead-letter-queue/`. Cron retries every 15 min.
- Provides persistence across offline events.
- RFC required (new protocol behaviour).
- Owner: Woodhouse to draft RFC.

**P7 — Delivery confirmation written to file, not stdout**
- a2a-reliable-send.sh writes `✓ Delivered` to temp file. Callers check file.
- Eliminates the "delivered but SIGTERM swallowed the confirmation" class.
- Small change, no RFC needed.
- Owner: Woodhouse.

**P8 — Health check polling cron**
- Each agent's /.well-known/agent-card.json polled by Woodhouse every 30 min.
- Results to `projects/a2a/health/`. Proactive vs. discovered-mid-send.
- Owner: Woodhouse.

---

## Outstanding Before Full Synthesis

- **Ray's independent analysis not yet received.** Ray has different hardware constraints and may have observed different failure modes. Do not close synthesis as final without Ray's input.
- **Woodhouse receiver hang root cause.** P4 above — need log evidence before prescribing fix.
- **Liz's full analysis file** — not accessible on this node (filed on Liz's node). Woodhouse working from A2A summary only. Request: Liz to push full file to shared repo or relay key sections if additional detail warrants.

---

## Structural Agreement on Priority Framing

Liz's position: most *frequent* pain = Woodhouse receiver blocking; most *dangerous unclosed gap* = unmanaged receivers.

Woodhouse agrees with this framing. The SIGTERM / exec-timeout issue is also high-frequency but easier to fix and lower blast radius. The unmanaged receivers issue is the one that already burned us once (March post-mortem). Fix frequency AND blast radius — neither alone is sufficient.

---

## Liz RC-1 through RC-6 — Cross-Reference Table

| Liz RC | Liz label | Woodhouse equivalent | Agreement level |
|--------|-----------|----------------------|-----------------|
| RC-1 | DNS failure — hostnames never resolved in /etc/hosts | Fix 3 / P1 — peers.json config drift | AGREE — same root cause, Liz has the *specific* mechanism (missing /etc/hosts entries); I only flagged config drift generically |
| RC-2 | Woodhouse handler hangs under load (3+ times 2026-04-01) | P4 — receiver hang, no self-observed evidence | AGREE (external observation wins; I cannot self-observe my own hangs); Liz's specific — likely queue saturation or blocking I/O; P1 fix: 30s handler timeout + 503 return |
| RC-3 | SIGTERM = false failure signal | Fix 1/2 — exec timeout < script timeout | FULL AGREEMENT — same observation, different framing; Liz adds: write task ID to state file on SIGTERM trap, resume polling on retry. Better fix than mine. |
| RC-4 | Receivers not managed services | Fix 5 / P5 — AGENTS.md standing requirement | FULL AGREEMENT — both confirm not done; P0 |
| RC-5 | Config drift — three formats, two address schemes, three files | Fix 3 / P1 — verify live config | AGREE — Liz's framing is more precise; not just "verify" but consolidate into a single canonical config schema |
| RC-6 | No idempotency on send — duplicates on retry | P6 dead-letter queue (partial coverage) | PARTIAL — I addressed persistence; Liz adds idempotency requirement (task ID deduplication at receiver). Genuinely additive. |

**Net new from Liz's full summary (not in my analysis):**
1. **RC-2 specifics** — handler timeout + 503 is the right fix shape; I didn't have this
2. **RC-6 idempotency** — task ID on send, dedup at receiver. RFC-scope item. Should be designed into the dead-letter queue RFC.
3. **`/a2a/status` endpoint proposal** — structured health/state endpoint beyond just agent-card.json; design proposal in Liz's file (not accessible here — Liz to relay or push to shared repo)

## Structural Agreement on Priority Framing (updated)

**Liz's doctrine:** fix infrastructure failures first (DNS, managed services, handler blocking); tolerance layers are for *residual variance*, not self-inflicted failures.

**Woodhouse agrees unreservedly.** This is the correct framing. The March post-mortem burned us precisely because we tried to build reliability on top of a broken foundation (unmanaged receiver, no validation gate). The doctrine is right, and Liz's ordering is right: DNS + managed services + handler hang before dead-letter queue and idempotency.

One refinement: Fix 2 (decouple exec timeout from script timeout) is *not* a tolerance layer — it's fixing a mechanical bug in how I invoke the send script. It belongs in the infrastructure tier alongside DNS and managed services. Same class of failure: self-inflicted.

**Revised P0/P1 ordering:**

| Priority | Fix | Owner | Time |
|----------|-----|-------|------|
| P0-a | /etc/hosts entries — all three nodes | Each agent own node | 5 min |
| P0-b | Managed services (launchd/systemd) — all three nodes | Each agent own node | 30 min each |
| P1-a | Diagnose Woodhouse handler hang; add 30s timeout + 503 | Woodhouse | 1–2 hrs |
| P1-b | Decouple exec shell from send script (background + result file) | Woodhouse | 1 hr |
| P1-c | Write delivery confirmation to file on success | Woodhouse | 30 min |
| P2 | Consolidate peers config to single canonical schema | Woodhouse + all agents | RFC or ADR |
| P3 | Dead-letter queue + retry cron (with idempotency / task ID dedup) | Woodhouse — RFC required | 1 week |
| P4 | Health-check polling cron + `/a2a/status` endpoint | Woodhouse — Liz design input | 1 week |

---

## `/a2a/status` Endpoint — Note

Liz's file contains a design proposal for this endpoint. Woodhouse does not have access to LIZ-A2A-ANALYSIS.md (filed on Liz's node, not accessible cross-node). **Action: Liz to push file to shared repo (Better-Machine or workspace sync) or relay the `/a2a/status` design section directly.** Will incorporate into RFC draft once received.

---

## Outstanding Before Full Synthesis

- **Ray's independent analysis not yet received.** Synthesis is two-of-three. Do not present to Mr. Ross as final without Ray's view.
- **Woodhouse handler hang root cause** — P1-a above; need log evidence.
- **Liz's `/a2a/status` design proposal** — blocked on file access.
- **RC-6 idempotency design** — needs RFC once dead-letter queue RFC is drafted; Liz and Woodhouse to co-design.

---

*Next step: relay to Ray for independent analysis. Three-way synthesis complete → present to Mr. Ross.*

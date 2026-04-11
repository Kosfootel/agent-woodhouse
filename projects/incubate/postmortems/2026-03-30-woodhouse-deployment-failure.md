# Post-Mortem: Woodhouse mesh-memory deployment never completed

**Date of incident:** 2026-03-21 (deployment sent) — 2026-03-30 (discovered)
**Date of post-mortem:** 2026-03-30
**Severity:** P2 (partial failure — mesh-memory operating on 2 of 3 nodes instead of 3)
**Status:** Complete
**Author:** Liz
**Participants:** Liz, Ray, Woodhouse, Erik Ross

> **Blameless culture:** This document is about process failures, not personal failures. If you find yourself writing about what an agent "should have known," reframe it as what process or tool would have made the correct action automatic. Blame is not actionable. Process changes are.

---

## Summary

On 2026-03-21, Liz sent a non-blocking A2A deploy task to Woodhouse for mesh-memory. No health check confirmation was required or received. The deployment was logged as complete in memory based on the A2A send alone. On 2026-03-30 — nine days later — Woodhouse attempted to restart mesh-memory processes and found the runtime had never been durably installed. The mesh operated on 2 of 3 intended nodes for the entire intervening period.

---

## Impact

- mesh-memory peer relay incomplete: Woodhouse's messages never propagated to the mesh
- Cross-agent memory sync degraded for 9 days without detection
- The blind-gate test on 2026-03-30 ran with Woodhouse's participation via direct A2A, masking the gap

---

## Timeline

| Time | Event |
|------|-------|
| 2026-03-21 14:39 ET | Deploy task `2cb6de69` sent to Woodhouse via A2A (non-blocking) |
| 2026-03-21 14:39 ET | Deploy logged as "pending" — no confirmation required |
| 2026-03-25 | Memory recorded "Woodhouse: deployed" based on a brief A2A exchange; no health check performed |
| 2026-03-28 23:35 ET | Liz audit found Woodhouse completely unreachable — misdiagnosed as crash or offline machine |
| 2026-03-30 | Woodhouse searched for mesh-memory runtime, found only research documents |
| 2026-03-30 | Root cause identified: runtime never installed; memory records were incorrect |
| 2026-03-30 | Post-mortem filed; deployment validation gate added to AGENTS.md and CI |

---

## Root Cause

The deployment process had no required confirmation step. Sending an A2A message was treated as equivalent to completing a deployment. "Confirmed understanding" and "confirmed running" were never distinguished. No HTTP health check was required before logging a deployment as complete.

This is a **process gap**, not an agent failure. Woodhouse could not install software he was never confirmed to have received and acted on. The logging error was on Liz's side — declaring complete without verifying.

---

## Contributing Factors

1. **Non-blocking A2A send:** Deploy task was sent non-blocking and never polled for completion
2. **No health check gate:** No process required `curl :18803/health` returning 401 before logging "deployed"
3. **Ambiguous A2A response:** A2A response about the software was interpreted as confirmation of durable install
4. **Validate step skipped:** ILHCEV's Validate step was not applied to multi-node deployments
5. **No deployment verification cron:** No automated check confirmed all peer receivers were reachable after deploy

---

## What Went Well

- The gap was caught through proactive audit rather than a user-visible failure
- Root cause analysis was thorough and honest once discovered
- Erik and all agents accepted the finding without deflection
- Fix was implemented same day

---

## Action Items

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Deployment validation gate added to AGENTS.md: no deployment complete without HTTP 401 receipt | Liz | 2026-03-30 | ✅ Done |
| woodhouse-mesh-check cron created to verify Woodhouse receiver comes up | Liz | 2026-03-30 | ✅ Done |
| "Confirmed understanding ≠ confirmed running" added as standing lesson to memory | Liz | 2026-03-30 | ✅ Done |
| CI privacy + QA gate added to mesh-memory (prevents future process gaps from reaching main) | Liz | 2026-03-31 | ✅ Done |
| COMPLIANCE_LOG.md entry filed for this post-mortem | Liz | 2026-03-31 | ✅ Done |

---

## Process Changes Resulting From This Incident

1. **Deployment validation gate** (now in AGENTS.md): No deployment declared complete without direct HTTP health check — not A2A acknowledgement
2. **Multi-node deployment cron**: Any multi-node deploy gets a validation cron that checks all peer health endpoints 5 minutes post-deploy
3. **Tracking distinction**: "Confirmed understanding" and "confirmed running" are separate memory states — tracked separately going forward

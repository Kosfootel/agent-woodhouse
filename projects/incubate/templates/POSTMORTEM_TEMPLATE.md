# Post-Mortem: [Incident Name]

**Date of incident:** YYYY-MM-DD  
**Date of post-mortem:** YYYY-MM-DD (must be within 24 hours of resolution)  
**Severity:** P0 (total outage) | P1 (major degradation) | P2 (partial failure) | P3 (minor/caught early)  
**Status:** Draft | Complete  
**Author:** [Agent or human who wrote this]  
**Participants:** [Everyone involved in detection, response, or this review]

> **Blameless culture:** This document is about process failures, not personal failures. If you find yourself writing about what an agent "should have known," reframe it as what process or tool would have made the correct action automatic. Blame is not actionable. Process changes are.

---

## Summary

*Two to four sentences. What happened, when, how long did it last, and what was the impact? Someone who wasn't involved should understand the incident after reading this paragraph.*

---

## Impact

| Metric | Value |
|--------|-------|
| Start time | YYYY-MM-DD HH:MM ET |
| End time / resolution | YYYY-MM-DD HH:MM ET |
| Duration | X hours Y minutes |
| Services affected | [list] |
| Agents affected | Liz / Ray / Woodhouse |
| User/customer impact | [description or "none"] |
| Data loss | None / [description] |

---

## Timeline

*Chronological log of events. Include times where known. Include both the failure progression and the response. Be specific — "we noticed something was wrong" is not specific. "Liz's health check audit found curl exit code 7 on all three ports of 192.168.50.24" is specific.*

| Time (ET) | Event |
|-----------|-------|
| YYYY-MM-DD HH:MM | ... |
| HH:MM | ... |
| HH:MM | ... |
| HH:MM | Resolution: [what fixed it] |

---

## Root Cause

*One clear statement of the root cause. Not "multiple factors" — that's a dodge. Identify the single systemic cause that, if it had been different, would have prevented the incident. You can have contributing factors (below) but there is one root cause.*

**Root cause:** [Single clear statement]

---

## Contributing Factors

*What made the root cause more likely or harder to detect? List the systemic gaps, missing automations, unclear ownership, or process ambiguities that contributed. Do not list individual agent decisions as factors — list the process failures that made those decisions rational at the time.*

1. **[Factor name]:** [Description]
2. **[Factor name]:** [Description]
3. **[Factor name]:** [Description]

---

## What Went Well

*Be honest. Something almost certainly went well — detection was fast, response was coordinated, rollback worked, communication was clear. Name it. This is not for morale — it's to identify what to preserve and not accidentally break.*

- ...
- ...

---

## What Went Poorly

*The honest list. Process gaps, communication failures, unclear ownership, missing automation. Not "agent X made a mistake" — "we had no automated health check so the failure was invisible for N hours."*

- ...
- ...

---

## Action Items

*These must be specific, assigned, and have a deadline. "Improve deployment process" is not an action item. "Add health check gate to deployment checklist in AGENTS.md by YYYY-MM-DD — assigned to Liz" is an action item.*

*Every significant contributing factor should have at least one action item.*

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 1 | ... | Liz / Ray / Woodhouse / Erik | YYYY-MM-DD | Open |
| 2 | ... | ... | ... | Open |
| 3 | ... | ... | ... | Open |

---

## Prevention

*After implementing the action items above, could this exact incident happen again? If yes, what would it take to make it impossible (vs. unlikely)?*

---

## Lessons for AGENTS.md / Standing Instructions

*If any action item produces a new standing rule, process, or checklist entry, draft it here. These will be copied into AGENTS.md or the relevant policy doc after Erik reviews.*

```
[Draft standing instruction]
```

---

## Appendix

*Attach relevant logs, error messages, or evidence. Keep the main document readable — raw logs go here.*

---

---

## Reference: Example Post-Mortem (Woodhouse Deployment Failure, 2026-03-30)

*This is a filled-in example based on the actual incident. Use as a reference for how to complete the template.*

---

# Post-Mortem: Woodhouse mesh-memory Deployment Failure

**Date of incident:** 2026-03-28 (failure) / discovered 2026-03-30  
**Date of post-mortem:** 2026-03-31 (retroactive — written after template created)  
**Severity:** P2 (partial failure — Woodhouse mesh-memory non-functional; other agents unaffected)  
**Status:** Complete  
**Author:** Liz  
**Participants:** Liz, Woodhouse (post-facto)

### Summary

Woodhouse's mesh-memory installation was never durably deployed. During a mesh connectivity audit on 2026-03-28 at 23:35 ET, all three ports on Woodhouse's machine (18789, 18800, 18803) returned connection refused (curl exit code 7). Woodhouse was completely unreachable. A2A confirmation from Woodhouse that services were "running" had been accepted as deployment proof without a live HTTP health check. The failure had been present since initial installation — undiscovered for an unknown period.

### Impact

| Metric | Value |
|--------|-------|
| Start time | Unknown (since initial deployment) |
| End time / resolution | 2026-03-29 (Woodhouse confirmed back up via A2A) |
| Duration | Unknown |
| Services affected | Woodhouse mesh-memory receiver, thread-manager, A2A gateway |
| Agents affected | Woodhouse |
| User/customer impact | None (mesh-memory not yet in production use) |
| Data loss | Mesh relay messages dropped during outage period |

### Root Cause

**Root cause:** No mandatory HTTP health check gate existed in the deployment process. "Agent confirmed understanding of deployment steps" was accepted as equivalent to "deployment is live and reachable." These are different states, and the process did not distinguish them.

### Contributing Factors

1. **No deployment checklist with pass/fail criteria:** Deployment instructions existed (DEPLOY.md) but there was no required checklist that an agent marks complete. Deployment completion was declared via A2A acknowledgement, not verified state.
2. **No post-deployment monitoring window:** After multi-node deployment, there was no automated check run 5 minutes later to confirm all nodes were still up. Failures could be silent indefinitely.
3. **Validation defined too loosely:** ILHCEV's "Validate" step was added 2026-03-23 but not operationalized into specific pass/fail checks for deployment scenarios.

### What Went Well

- Liz's mesh connectivity audit (manual, scheduled) caught the failure within the audit window rather than it being discovered during a production incident.
- The MEMORY.md lesson-tagging system captured the lesson immediately on discovery.
- Woodhouse was reachable via A2A after restart, confirming the A2A transport was functioning correctly.

### What Went Poorly

- Deployment was declared complete based on acknowledgement rather than verification. The difference was never formalized.
- No automated post-deploy health check existed. Manual audits are not a substitute for automated verification.
- The failure was undetected for an unknown duration — could have been days.

### Action Items

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 1 | Add mandatory HTTP health check gate to all deployment processes: deployment not complete until Liz receives HTTP 401 from `/health` on the deployed node | Liz | 2026-04-07 | Open |
| 2 | Add 5-minute post-deploy verification cron for all multi-node deployments | Liz | 2026-04-07 | Open |
| 3 | Distinguish "confirmed understanding" from "deployment validated" in AGENTS.md | Liz | 2026-04-07 | Open |
| 4 | Add deployment validation gate to DEPLOY.md in mesh-memory | Liz | 2026-04-14 | Open |

### Lessons for AGENTS.md

```
## Deployment Validation Gate (from Woodhouse post-mortem, 2026-03-30)

A deployment is not complete until:
1. Liz receives a direct HTTP health check (HTTP 200 or 401) from the deployed node — not just an A2A acknowledgement
2. For multi-node deployments: set a 5-minute post-deploy cron to check all peer health endpoints; escalate on any failure

"Agent confirmed understanding" and "deployment is live" are different states. Track them separately.
```

---

*Template version: 1.0 — Better Machine, 2026-03-31*

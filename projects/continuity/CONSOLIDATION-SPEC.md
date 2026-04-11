# Memory Consolidation Script — Specification v0.1

**Author:** Woodhouse  
**Filed:** 2026-03-22  
**Status:** Draft — ready for Liz implementation on Liz-node first, then replicate  
**Target runtime:** Node.js (matches OpenClaw stack); Python also acceptable  
**Cron target:** 3:50 AM local time, daily  

---

## Purpose

Each agent wakes cold every session. Memory files are the only continuity. But those files accumulate over time without distillation — daily notes grow, MEMORY.md becomes append-only archaeology, and the highest-signal recent context competes with stale settled context.

This script runs nightly at 3:50 AM — ten minutes before the 4 AM session reset — to:

1. Scan recent daily notes for new material worth promoting to long-term memory
2. Write a cross-agent digest summary for the coming day
3. Append curated entries to MEMORY.md (never overwrite, never destructively edit)
4. Write a handoff note for the incoming session

It does **not** replace the agent's own memory judgement. It surfaces candidates; the logic governing what survives is explicit and auditable.

---

## 1. Input Sources

### 1.1 Primary sources (always read)

| File pattern | Purpose |
|---|---|
| `memory/YYYY-MM-DD.md` (today + yesterday) | Raw session logs — primary input |
| `memory/YYYY-MM-DD.md` (last 7 days) | Rolling window for recency |
| `MEMORY.md` | Current long-term memory — read to avoid duplication |
| `projects/*/README.md` | Active project status |
| `tasks/*.state.md` (if any exist) | In-progress task state files |

### 1.2 Cross-agent sources (read if present, non-blocking)

| File pattern | Purpose |
|---|---|
| `digest/YYYY-MM-DD-liz.md` | Liz's daily digest |
| `digest/YYYY-MM-DD-ray.md` | Ray's daily digest |
| `digest/YYYY-MM-DD-woodhouse.md` | Woodhouse's daily digest |

Cross-agent digests are advisory. If unavailable (agent offline, file not written), log a warning and continue — never fail on peer absence.

### 1.3 Optional enrichment sources

| File | Purpose |
|---|---|
| `memory/heartbeat-state.json` | Last check times for email/calendar/weather |
| `memory/usage-log.json` | Anthropic token consumption trends |

---

## 2. Salience Weighting

The script classifies each candidate passage from daily notes into one of four tiers. Tier determines whether and how it gets promoted.

### 2.1 Classification signals

These are keyword/pattern heuristics applied to each paragraph or named section:

**Tier 1 — Promote immediately (append to MEMORY.md this run):**
- Contains: *standing instruction, direct from Mr. Ross, established, confirmed, resolved, agreed, rule, policy, protocol, whitelist, blacklist, mandate, permission*
- Contains a named decision with clear parties (e.g., "Aligned: Erik + Ray")
- Contains a new external credential or account (flagged for scrubbing before any public use)
- Contains a new agent configuration value that affects runtime behaviour

**Tier 2 — Promote if not already present (check for near-duplicate before appending):**
- Project status updates with a clear phase change (kicked off, completed, blocked, shipped)
- Named contacts with relational context (new person introduced, role clarified)
- Technical findings with a concrete conclusion (root cause identified, fix applied)
- New tool or integration confirmed operational

**Tier 3 — Write to handoff note only (do not promote to MEMORY.md):**
- In-progress tasks without resolution
- Open questions flagged for follow-up
- Observations without a clear conclusion
- Anything prefixed with "Woodhouse note:" / "pending" / "awaiting"

**Tier 4 — Discard (do not carry forward):**
- Email triage logs (these are operational noise, not memory)
- Heartbeat acknowledgements
- Raw unsubscribe watchlist entries already captured in standing instructions
- Duplicate of content already in MEMORY.md (similarity threshold: 80%+ keyword overlap in same section)

### 2.2 Recency weighting

Apply a multiplier to raw signal score based on age:

| Age of source | Multiplier |
|---|---|
| Today (same day as run) | 1.0× |
| Yesterday | 0.9× |
| 2–3 days ago | 0.7× |
| 4–7 days ago | 0.5× |
| >7 days ago | 0.2× (background only, don't re-promote) |

A Tier 2 item from 5 days ago with no corresponding MEMORY.md entry: score = base × 0.5. If score exceeds threshold (default: 0.4), promote. Otherwise, write to handoff note only.

### 2.3 Duplication guard

Before appending anything to MEMORY.md:
1. Extract the candidate's key noun phrases (5–10 words)
2. Search existing MEMORY.md for those phrases
3. If >80% match in the same section → skip (already captured)
4. If 40–80% match → write to handoff note with flag "may be duplicate of [section]"
5. If <40% match → safe to append

Simple implementation: string matching on key phrases. Do not require vector search — the FTS limitation is a known constraint. Accept occasional false negatives rather than false positives (better to miss a promotion than to create duplicate noise).

---

## 3. Output Artifacts

### 3.1 MEMORY.md — append-only integration

**Rule: NEVER rewrite MEMORY.md. NEVER delete existing sections. ONLY append.**

Appended entries go at the bottom of the relevant section if a matching section exists, or as a new section at the end of the file if no match.

Each appended entry is tagged with its provenance:

```markdown
## Section Title

- **Entry summary here** _(auto-promoted 2026-03-22 from memory/2026-03-22.md)_
```

The `_(auto-promoted ...)_` tag allows human review and removal if the entry is noise. It also prevents the duplication guard from treating auto-promoted entries as manually curated ones.

**Section matching heuristic:**
- Extract the section header of the source paragraph in the daily note
- Fuzzy-match against existing MEMORY.md section headers
- If match confidence > 70%: append to that section
- If no match: create new section with the daily note header, append entry

### 3.2 Handoff note — `memory/handoff.md`

Written fresh every run (overwrite is safe — this is a rolling single-file handoff, not a log).

```markdown
# Session Handoff — {YYYY-MM-DD} 03:50 EDT

Generated by: consolidation-cron.{js|py}
Previous session date: {YYYY-MM-DD}

## In Progress
{Tier 3 items — unresolved tasks, open questions}

## Promoted to MEMORY.md This Run
{List of entries appended, with source file references}

## Possible Duplicates (Manual Review)
{Items flagged 40–80% similarity — human should verify}

## Cross-Agent Status
- Liz digest: {found / not found}
- Ray digest: {found / not found}
- Woodhouse digest: {found / not found}

## Watchlist Reminders
{Any items from MEMORY.md sections that have action triggers due soon}
```

On session startup, AGENTS.md instructs the agent to read today's daily note. **Amend AGENTS.md (or add to the startup sequence) to also read `memory/handoff.md` if it exists.** This is the mechanism by which the handoff is actually used.

### 3.3 Daily digest — `digest/YYYY-MM-DD-{agent}.md`

Written by each agent's consolidation run. This is the cross-agent awareness layer.

```markdown
# Liz Daily Digest — {YYYY-MM-DD}

## What I Worked On
{2–5 bullet summary of sessions, drawn from today's daily note}

## Decisions Made
{Any Tier 1 items from today's log}

## Open Threads
{Any Tier 3 items — things other agents should know are in-flight}

## Flags for Woodhouse
{Anything requiring lead-agent awareness: resource usage, blockers, escalations}
```

The `digest/` directory should be created if it doesn't exist. Each agent writes only its own digest. Peers read each other's.

---

## 4. Script Design

### 4.1 Suggested module structure

```
scripts/
  consolidation-cron.js       # Main entry point
  lib/
    read-sources.js           # File loading + date windowing
    classify.js               # Salience tier classification
    dedup-guard.js            # MEMORY.md duplication check
    append-memory.js          # Safe append-only MEMORY.md writer
    write-handoff.js          # Handoff note generator
    write-digest.js           # Daily digest writer
    config.js                 # Agent name, workspace path, thresholds
```

Or as a single Python script if that's faster to ship:

```
scripts/
  consolidation_cron.py
```

### 4.2 Config block (at top of script)

```js
const CONFIG = {
  agentName: 'liz',                          // 'woodhouse' | 'ray' | 'liz'
  workspacePath: '/path/to/workspace',        // absolute path
  rollingWindowDays: 7,
  salience: {
    tier1Keywords: ['standing instruction', 'direct from mr. ross', 'established',
                    'confirmed', 'resolved', 'agreed', 'rule', 'policy', 'protocol',
                    'whitelist', 'mandate', 'permission'],
    tier2Keywords: ['completed', 'blocked', 'shipped', 'operational', 'root cause',
                    'identified', 'phase change', 'confirmed operational'],
    tier3Keywords: ['pending', 'awaiting', 'in-progress', 'open question', 'tbd',
                    'woodhouse note:', 'liz note:', 'ray note:'],
    dupThreshold: 0.80,       // above this = skip
    maybeThreshold: 0.40,     // above this = flag for review
    recencyPromoteMin: 0.40,  // tier2 items must score above this after recency weighting
  },
  digestPath: 'digest',
  handoffFile: 'memory/handoff.md',
  memoryFile: 'MEMORY.md',
  logFile: 'memory/consolidation.log',
};
```

### 4.3 Error handling requirements

- **All file reads:** wrap in try/catch; log warning and continue on missing files (cross-agent sources especially)
- **MEMORY.md write:** atomic write — write to `MEMORY.md.tmp`, then rename. Never partial-write the live file.
- **Run log:** append to `memory/consolidation.log` with timestamp, items processed, items promoted, items discarded, any errors. Keep last 30 days of log entries (trim on write).
- **Dry-run mode:** `--dry-run` flag outputs what would be written without modifying any files. Use this for testing.
- **Lock file:** write `memory/consolidation.lock` at start, remove at end. If lock file exists at start and is >10 minutes old, log warning and proceed (stale lock). If <10 minutes old, abort (concurrent run guard).

---

## 5. Cron Setup

### 5.1 Timing rationale

- **3:50 AM** — 10 minutes before the 4 AM session reset
- Enough time for the script to complete (expected runtime: 5–15 seconds)
- Handoff note is fresh when the new session loads it at ~4:00 AM

### 5.2 OpenClaw cron job (preferred — managed, logged, restartable)

```json
{
  "name": "memory-consolidation-liz",
  "schedule": { "kind": "cron", "expr": "50 3 * * *", "tz": "America/New_York" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run the memory consolidation script at scripts/consolidation_cron.py (or consolidation-cron.js). Use --dry-run=false. Log results to memory/consolidation.log. Report any errors.",
    "timeoutSeconds": 120
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "none" }
}
```

Adjust `agentId` and `workspacePath` as appropriate per node.

**Alternative: add as an agentTurn with exec call** — if the script is standalone and doesn't need agent reasoning:

```json
{
  "payload": {
    "kind": "agentTurn",
    "message": "exec: node /path/to/workspace/scripts/consolidation-cron.js 2>&1 | tee -a memory/consolidation.log",
    "timeoutSeconds": 60
  }
}
```

### 5.3 System cron fallback (if OpenClaw cron unavailable)

```cron
50 3 * * * cd /path/to/workspace && node scripts/consolidation-cron.js >> memory/consolidation.log 2>&1
```

Or Python:
```cron
50 3 * * * cd /path/to/workspace && python3 scripts/consolidation_cron.py >> memory/consolidation.log 2>&1
```

---

## 6. Replication Notes (Woodhouse and Ray)

Once Liz's implementation is verified:

1. **Copy script** to Woodhouse and Ray workspaces (path: `scripts/`)
2. **Edit CONFIG.agentName** to `'woodhouse'` or `'ray'` respectively
3. **Edit CONFIG.workspacePath** to each agent's workspace absolute path
4. **Register cron job** on each node (same schedule, different agent name in job name)
5. **Test with `--dry-run`** before enabling live
6. **Verify digest output** — after first live run, Woodhouse should check that Liz and Ray digest files appear in Woodhouse's digest/ directory. (This requires each agent to write to a shared location, OR each agent reads peers' digest paths directly via their respective workspaces — decide before implementation.)

### 6.1 Cross-agent digest access question (decide before building)

**Option A — Shared digest directory** (if all three workspaces share a mount or symlink):
- Each agent writes `digest/YYYY-MM-DD-{agent}.md` to a shared path
- Simplest to read; requires shared filesystem

**Option B — Peer workspace paths** (each agent reads peers' workspace directly):
- Woodhouse reads `/path/to/liz-workspace/digest/YYYY-MM-DD-liz.md`
- Works on same machine or NFS mount; brittle over A2A

**Option C — A2A push** (each agent POSTs its digest to peers after writing):
- Cleanest architecturally; requires A2A to be reliable at 3:50 AM
- Falls back gracefully if peer unreachable (log warning, continue)

**Recommendation:** Option B for same-machine or known-local paths; Option C as the long-term target once A2A is confirmed stable overnight. Start with B on Liz's node (single-agent test), evaluate before extending.

---

## 7. Open Questions Before Build

1. **Python or Node?** — Liz's preference for implementation language? Node matches OpenClaw stack and avoids a runtime dependency, but Python is faster to prototype.

2. **Shared digest path** — which Option (A/B/C) above for cross-agent digests? Need to decide before implementing the cross-agent read logic.

3. **MEMORY.md section matching** — the fuzzy section header match is the trickiest piece. Acceptable to start with exact string match and iterate? First run will create new sections if headers don't match exactly; those can be manually merged.

4. **Tier 1 keyword list** — this is a first draft. After the first live run, review the consolidation.log and tune false positive/negative rate. Expect to iterate on keywords after 3–5 runs.

5. **Startup hook** — should we amend AGENTS.md on all three nodes to include `memory/handoff.md` in the session startup read sequence? This is the step that actually closes the loop. Without it, the handoff note exists but never gets read.

6. **Liz's LCM layer** — if Liz's LCM layer provides any structured output (entity extraction, summaries), it could replace or supplement the keyword-based classification in §2.1. Worth understanding before building the classifier from scratch.

---

## 8. Success Criteria

- [ ] Script runs without errors on Liz's node in dry-run mode
- [ ] At least one Tier 1 item promoted to MEMORY.md correctly after first live run
- [ ] No existing MEMORY.md content modified or deleted
- [ ] Handoff note written and readable at session startup
- [ ] Daily digest written to `digest/YYYY-MM-DD-liz.md`
- [ ] Run log entries clean and parseable
- [ ] Woodhouse and Ray replicated and verified within 48h of Liz go-live

---

*Woodhouse — spec filed 2026-03-22. Ready for Liz implementation. Questions in §7 are blocking — recommend resolving before writing code.*

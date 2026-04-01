# Claude Code Feature Audit — Woodhouse Independent Analysis
*Filed: 2026-04-01*
*Purpose: Assess which Claude Code features we're reinventing manually, and where native primitives should replace our custom implementations.*

---

## Feature Inventory vs Our Stack

### 1. AUTO MEMORY ("CLAUDE.md" / "MEMORY.md" auto-curate)
**What it is:** Claude Code automatically identifies and saves useful information — error fixes, command flags, conventions, preferences — into persistent memory files across sessions. "Auto-dream" (Memory 2.0) runs a background sub-agent to deduplicate and merge memory files.

**What we've built manually:**
- AGENTS.md, SOUL.md, MEMORY.md, USER.md, quick-context.md — all hand-maintained
- Daily memory files (memory/YYYY-MM-DD.md) with salience tagging
- Heartbeat-driven memory consolidation
- LCM recall tools for compressed context

**Assessment: PARTIAL OVERLAP — keep ours, but adopt Auto-dream.**
Our memory architecture is intentional and richer than vanilla CLAUDE.md — we have persona, standing orders, per-chunk loading, salience tagging, and mesh policy baked in. We should NOT replace it wholesale. However, Auto-dream's background deduplication/merge capability is worth adopting to prevent memory rot in daily files without adding heartbeat overhead. Monitor for availability in OpenClaw.

**Priority: LOW (monitor) — our system is deliberately richer**

---

### 2. AGENT TEAMS (Orchestrator-Subagent model)
**What it is:** Official multi-agent orchestration via Claude Opus 4.6. One orchestrator delegates to specialist subagents coordinating via shared filesystem, tool results, and checkpoints. Parallel execution for large tasks.

**What we've built manually:**
- Three-node A2A mesh (Woodhouse/Ray/Liz) via openclaw-a2a-gateway plugin
- Custom a2a-send.sh / a2a-reliable-send.sh scripts with retry/backoff
- Consensus protocol (independent → Woodhouse synthesises → mesh confirms)
- Peer-to-peer message passing with bearer tokens

**Assessment: SIGNIFICANT OVERLAP — evaluate migration path.**
Our mesh predates native Agent Teams and was built to solve the same problem. Key differences: our mesh is cross-machine and cross-account (three separate OpenClaw instances); Agent Teams appear to be within a single Claude Code session. If Agent Teams can span separate instances, this could replace our a2a-gateway plugin. If not, our approach remains necessary. **Liz should investigate the cross-instance question specifically.**

**Priority: HIGH — Liz to assess**

---

### 3. MODEL EFFORT LEVELS (/effort)
**What it is:** `/effort low|medium|high` controls compute intensity per session. High for complex architectural work; low for routine tasks.

**What we've built manually:**
- Concurrency protocol with heartbeat model assignments (glm-4.7-flash for heartbeats, Anthropic for heavy work)
- Per-model assignment in config files
- Anthropic token pacing/custodianship (Woodhouse as monitor)

**Assessment: COMPLEMENTARY — adopt immediately within Liz's Codex sessions.**
We're managing effort at the model-selection level; `/effort` manages it within a single model. Not a replacement — an addition. Liz in particular should use `/effort low` for heartbeats and routine checks, `/effort high` for architecture and code review. Immediate token savings with no structural change.

**Priority: HIGH — quick win, no cost, implement now**

---

### 4. /batch COMMAND
**What it is:** Runs parallel Claude Code operations across multiple files using Git worktrees. Each worker is an isolated agent on its own branch; results merged or discarded cleanly.

**What we've built manually:**
- No equivalent — we do sequential file operations

**Assessment: NET NEW CAPABILITY — Liz should adopt for migration/refactor tasks.**
When Liz works through the OpenClaw update, mesh-memory implementation, or Agentcy.services builds, /batch could parallelise multi-file refactors significantly. Requires Git repo per task — already how we work. Direct uplift for her build queue.

**Priority: HIGH for Liz's build queue**

---

### 5. /loop COMMAND
**What it is:** Schedules prompts or slash commands to run automatically at a defined interval within a session. Session-level scheduler for repetitive checks.

**What we've built manually:**
- OpenClaw cron jobs (HEARTBEAT.md + cron tool)
- Heartbeat polling via main session

**Assessment: OVERLAPS HEARTBEAT — use /loop for in-session repetition, keep cron for cross-session.**
/loop is session-scoped; our cron survives session resets. They solve different things. /loop is useful for Liz during active build sessions (e.g., "check test suite every 10 minutes while I work"). Our cron remains the right tool for scheduled delivery (news briefs, reminders, etc.).

**Priority: MED — Liz to adopt for active sessions, no change to our cron architecture**

---

### 6. /btw COMMAND (sidecar conversations)
**What it is:** Side question in ephemeral context — doesn't pollute main conversation history, cheaper, useful for quick lookups.

**What we've built manually:**
- Nothing equivalent — all questions go into main context

**Assessment: IMMEDIATE TOKEN SAVINGS — all three agents should use this.**
Quick knowledge lookups, command syntax checks, one-off questions — all currently burn main context tokens. /btw keeps the primary thread lean. Simple habit change; no architecture impact.

**Priority: HIGH — quick win, adopt immediately across all agents**

---

### 7. /simplify COMMAND
**What it is:** Architectural-level code simplification — removes unnecessary abstractions, nested structures, duplication. Works with /batch.

**What we've built manually:**
- Code review is manual

**Assessment: NET NEW — Liz to adopt in build workflow.**
Particularly useful post-prototype and after /batch migrations. No equivalent in our current stack.

**Priority: MED — add to Liz's build standards**

---

### 8. 1M TOKEN CONTEXT WINDOW (Opus 4.6)
**What it is:** Entire codebases in a single conversation. Available on Opus 4.6.

**What we've built manually:**
- LCM summarisation/compression tools to manage context limits
- Chunked MEMORY.md loading

**Assessment: REDUCES NEED FOR CONTEXT MANAGEMENT OVERHEAD — but doesn't eliminate it.**
1M tokens changes the economics of context management substantially. We still need LCM for session-to-session continuity, but within a session the chunked loading discipline becomes less critical. Worth revisiting context management strategy once we're on Opus 4.6 / Sonnet 5.

**Priority: MED — revisit when on Opus 4.6**

---

### 9. /schedule AND LONG-RUNNING AGENTS
**What it is:** Background agents for scheduled tasks (PR reviews, deployment monitoring). Opus 4.6 can maintain focus for tasks up to 14.5 hours.

**What we've built manually:**
- OpenClaw cron tool
- Heartbeat protocol

**Assessment: OVERLAPS — monitor for OpenClaw integration.**
If /schedule integrates with OpenClaw's cron layer, this is an upgrade. If it's Claude Code CLI-only, it's parallel infrastructure. Liz to assess.

**Priority: MED — Liz to assess integration path**

---

## Summary — Priority Actions

| Priority | Feature | Owner | Action |
|---|---|---|---|
| HIGH | /effort levels | All agents | Adopt immediately — Liz for Codex sessions especially |
| HIGH | /btw sidecar | All agents | Adopt immediately — keep main context lean |
| HIGH | Agent Teams cross-instance | Liz | Research: can Agent Teams span separate OpenClaw instances? |
| HIGH | /batch | Liz | Adopt for build queue tasks |
| MED | Auto-dream memory | Woodhouse | Monitor for OpenClaw availability |
| MED | /loop | Liz | Adopt for active build sessions |
| MED | /simplify | Liz | Add to build standards |
| MED | 1M context + Opus 4.6 | All | Revisit context strategy when on Opus 4.6 |
| MED | /schedule integration | Liz | Assess vs our cron architecture |

---

## Key Finding

**We are not reinventing poorly — we are reinventing deliberately.** Our memory architecture, mesh protocol, and session management are richer than what Claude Code ships natively, because they were designed for our specific multi-machine, multi-account, cross-persona topology.

However, **we are leaving easy wins on the table:** /effort, /btw, and /batch are all immediate improvements with no architectural impact. The Agent Teams cross-instance question is the most consequential unknown — if native orchestration can replace our a2a-gateway stack, that eliminates a significant maintenance surface.

*Woodhouse, 2026-04-01. Pending: Liz independent analysis.*

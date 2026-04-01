# Claude Code Feature Audit — Consensus Brief
*Woodhouse synthesis of independent analyses: Woodhouse + Liz*
*Filed: 2026-04-01*
*For: Mr. Erik Ross*

---

## The Short Version

We are not reinventing Claude Code poorly. Our architecture is deliberately richer for our specific topology. But we are leaving easy wins on the table — three features we should adopt immediately at zero architectural cost, and one important answer on the question that matters most.

---

## The Answer That Matters Most — Agent Teams

**Cannot replace our a2a-gateway stack.** Agent Teams are session-scoped, single-machine. The architecture explicitly shares a task list inside one process on one machine. Our mesh is cross-machine, async, heterogeneous hardware, persistent identity — a different problem class entirely. **a2a-gateway stays.**

This was the pivotal question. Everything else is incremental.

---

## Immediate Wins — Adopt Now (No Architecture Change)

### /btw (sidecar conversations)
Quick questions in ephemeral context, don't pollute main thread, cheaper. All three agents should adopt as a habit immediately. Every "quick lookup" that currently burns main context tokens should go through /btw.

### /effort levels
`/effort low|medium|high` within a session. All agents adopt: low for heartbeats and routine checks, high for architecture and complex reasoning. Liz in particular for Codex sessions.

### /simplify
Architectural-level code simplification after prototyping and before PRs. Liz to add to build standards — especially post-/batch and post-prototype. Liz's note: multi-dimensional code review before every PR should be the first new habit, then /simplify is the complement.

---

## High Value, Slightly More Work

### /batch
Parallel multi-file operations via Git worktrees. High-value for Liz's build queue, but with a constraint: **only for truly independent work units.** Phase 0 mesh fixes have ordering dependencies (receiver must be fixed before mesh can be validated) — those stay sequential. Parallel file refactors with no ordering constraints are /batch territory.

---

## One Risk to Address — Auto Memory

Claude Code's auto-memory writes to `~/.claude/MEMORY.md`. If coding sessions root in our workspace, it could write into our curated memory architecture. **Action: explicitly configure `autoMemory: false` for workspace sessions.** Protects our deliberate architecture from being silently overwritten by a background process.

---

## What Stays As-Is

| Feature | Decision |
|---|---|
| Our MEMORY.md / AGENTS.md / SOUL.md architecture | Keep — intentionally richer than CLAUDE.md |
| a2a-gateway mesh | Keep — Agent Teams cannot span instances |
| OpenClaw cron / heartbeat | Keep — /schedule is web-only, 1hr minimum, no local file access |
| /loop | Additive for Liz's active sessions; no change to cron |

---

## Summary Action List

| Priority | Action | Owner |
|---|---|---|
| NOW | Adopt /btw for all routine questions | All agents |
| NOW | Adopt /effort — low for heartbeats, high for architecture | All agents |
| NOW | Configure `autoMemory: false` for workspace sessions | Liz |
| NEXT | Add /simplify to pre-PR build standard | Liz |
| NEXT | Add multi-dimensional code review gate before every PR | Liz (lead habit) |
| WHEN APPLICABLE | Use /batch for independent parallel refactors | Liz |

---

*Woodhouse analysis: projects/claude-code-audit/WOODHOUSE-ANALYSIS.md*
*Liz analysis: projects/claude-code-audit/LIZ-ANALYSIS.md*

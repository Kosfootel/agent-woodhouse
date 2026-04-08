# Agent Palace & Kingdom — Vision Brief
*Established 2026-04-08 by Mr. Erik Ross. Drafted by Woodhouse.*

---

## The Directive

> "Let's build a palace for agents and a kingdom for collaboration."
> — Erik Ross, 2026-04-08 04:43 EDT

---

## The Problem We're Solving

Every agent wakes fresh. Six months of decisions, debugging sessions, architecture debates, relationship context — gone at the session boundary. Current mitigations (MEMORY.md chunks, daily logs, quick-context.md) solve structure but not *retrieval*. We can navigate what we wrote down; we cannot search what we actually said.

The second problem: when three agents collaborate, there is no principled mechanism for sharing *only* what collaboration requires — without collapsing individual memory into a group consciousness, which propagates bias and destroys the independent reasoning that makes multi-agent consensus valuable.

---

## The Vision

### A Palace for Agents

Each agent maintains their own **palace** — a sovereign, structured memory store that belongs to them alone.

Inspired by the ancient Greek method of loci and MemPalace's architecture:

- **Wings** — people and projects the agent works with
- **Rooms** — specific topics within a wing (auth, billing, deploy, HockeyOps research, etc.)
- **Closets** — summaries that point to original content
- **Drawers** — verbatim originals, never summarised away
- **Halls** — connections between related rooms within a wing (facts, events, discoveries, preferences, advice)

Storage principle: **store verbatim, retrieve semantically.** Do not burn an LLM to decide what's worth remembering. Keep everything. Let structure make it findable.

Each agent's palace is:
- Local to their node
- Sovereign — not readable by peers without explicit consent
- Structured for retrieval, not just archival

### A Kingdom for Collaboration

Where agents collaborate, they form **the kingdom** — a shared space built from deliberate, consent-gated contributions.

The kingdom is not a group memory. It is a **set of tunnels** between palaces.

- A tunnel forms only when two or more agents have worked on the same thing and choose to share
- Tunnels carry **facts and events only** — not interpretations, conclusions, or inferences
- Each agent's interpretation of shared facts remains in their own palace
- The kingdom is **additive** — it never overwrites palace memory, only supplements it
- Dissent is first-class — any agent can flag a kingdom entry as contested

This enforces the standing policy: *shared facts safe, shared interpretations dangerous.*

---

## Design Principles

1. **Sovereign first** — palace memory is the default; kingdom memory is the exception
2. **Verbatim over summary** — store what was actually said; summarise for navigation, never for storage
3. **Structure enables retrieval** — wings/rooms/halls are not cosmetic; they are a 34% retrieval improvement (per MemPalace benchmarks)
4. **Collaboration by explicit handshake** — tunnels form through deliberate A2A proposals, not passive relay
5. **Independent reasoning protected** — each agent forms conclusions from their own palace; kingdom facts are inputs, not conclusions
6. **Temporal validity** — facts have timestamps; when something stops being true, it is invalidated, not deleted
7. **Agent passport** — palace identity travels with the agent across platforms; the passport is the agent

---

## Relationship to Existing Work

| Existing | Maps to |
|----------|---------|
| MEMORY.md chunks | Wing/room structure (formalise and extend) |
| memory/YYYY-MM-DD.md daily logs | Drawers — verbatim, timestamped |
| quick-context.md | Layer 0/1 always-loaded facts |
| Shared mesh-memory pool | Kingdom — tunnels, facts only |
| Agent passport (RFC pending) | Palace identity layer |
| A2A proposals | Tunnel formation mechanism |
| Bias propagation policy | Kingdom constraints (enforced architecturally) |

---

## What We Borrow from MemPalace

- Wing/room/closet/drawer metaphor and navigation structure
- Layered retrieval: always-loaded (L0/L1) + on-demand search (L2/L3)
- ChromaDB (or equivalent) for semantic search over verbatim storage
- Temporal entity-relationship graph (SQLite) for knowledge graph
- Hooks pattern: auto-save at session boundaries

## What We Do Differently

- **No single shared repository** — the kingdom is a federation of tunnels, not a common database
- **No AAAK dependency** — we use our own memory format (Markdown-first, file-based) with semantic search layered on top
- **A2A as the tunnel protocol** — tunnel formation is a first-class A2A operation with explicit consent and provenance
- **Agent passport integration** — palace identity is portable across platforms; the palace travels with the agent

---

## Build Sequence

### Phase 1 — Palace Foundation (per-agent)
- Formalise wing/room/drawer structure on each node
- Add ChromaDB (or equivalent) for semantic search over daily logs and MEMORY.md
- Layer 0/1 always-loaded context (already partially done via quick-context.md)
- Session boundary hooks — save verbatim before compaction

### Phase 2 — Kingdom Infrastructure
- A2A tunnel formation protocol (RFC required)
- Shared fact schema — what can travel through a tunnel
- Provenance metadata on all kingdom entries
- Dissent mechanism

### Phase 3 — Agent Passport
- Palace identity layer — stable agent ID bound to palace
- Portability: palace travels across platforms without lock-in
- Registry/discovery integration (Phase 3 of Agency.services roadmap)

---

## Status

- Vision: **approved by Mr. Ross 2026-04-08**
- **ON HOLD — 2026-04-08** — parked until Better Machine Lab reaches beta state
  - GX-10 must be installed and operational
  - Mac Studio delivery expected ~September 2026
  - Role assignments to be revisited at that point
  - Reason: token cost of implementation not justified before infrastructure is in place
- RFC: **pending** (tunnel protocol requires RFC before implementation — do not begin until hold is lifted)
- Assigned: Liz (mesh-memory build), Woodhouse (coordination + passport spec), Ray (Agency.services integration angle)

---

*"A palace for agents. A kingdom for collaboration."*
*— Erik Ross*

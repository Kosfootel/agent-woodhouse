# ADR-0002: Personal Repository for Non-Canonical Work

## Status
**Accepted** — 2026-04-11

## Context
During Phase 2 repository consolidation, `BobbyRayBot-Internal` was identified as containing stray prompts, docs, and plans from past requests. Rather than merging into `agent-ray` (which would dilute Ray's operational repo) or deleting (which would lose potentially useful references), a dedicated personal repository is appropriate.

## Decision

### Repository Purpose
**Name:** `Human-Erik`
**Purpose:** Personal repository for Erik Ross's non-canonical artifacts
**Contents:**
- Stray prompts and prompt experiments
- Draft documents and plans
- Reference materials
- Ideas and notes not yet ready for formal project repos
- Personal tooling and utilities

### Why "Human-Erik"
- Distinguishes from agent repos (`agent-{name}` pattern)
- Clear ownership (Erik's personal space)
- Distinct from `erik-ross/` (which may be for administrative/decision records)

### Relationship to Other Repos
| Repo | Owner | Purpose |
|------|-------|---------|
| `Human-Erik` | Erik | Personal artifacts, drafts, experiments |
| `erik-ross/` | Erik | Administrative, decisions, governance |
| `agent-ray` | Ray | Operational agent workspace |

## Consequences
- **Positive:** Preserves access to historical artifacts
- **Positive:** Clear separation between agent work and personal work
- **Positive:** Erik has dedicated space for experimentation
- **Neutral:** Does not follow `agent-{name}` pattern (intentional)

## Implementation
- Rename `BobbyRayBot-Internal` → `Human-Erik`
- Keep private visibility
- No structural changes needed

# Memora — handoff to Liz (v0.2)

> Per master directive, 2026-07-01 11:27 EDT. Research brief at
> `research/2026-07-01-microsoft-memora/brief.md` (v0.2, re-issued
> 11:55 EDT after Liz's review of v0.1). This file is the handoff
> envelope so the routing is auditable.

## What I'm sending

- **Full research brief (v0.2):** `research/2026-07-01-microsoft-memora/brief.md`
  (267 lines; primary Microsoft Research blog URL + arXiv 2602.03315,
  verified numbers for both LoCoMo and LongMemEval, fleet implications,
  sources, honest caveats, revision history).
- **This envelope:** the routing metadata + the asks I am making of Liz.

## What changed in v0.2

Two corrections per Liz's review of v0.1:

1. **Numbers verified directly from the primary source.** Re-fetched
   the Microsoft Research blog at 11:50 EDT after the rate-limit
   window cleared, plus the arXiv 2602.03315 abstract. Added the
   87.4% LongMemEval number (missed in v0.1), the (S) variant
   84.9% LoCoMo, the 600-turn / 115K-token context sizes, and the
   344 vs 651 memory-entry comparison. §8 no longer says "I have
   not read the paper" — the abstract verifies the high-level claim.
2. **§7.1 Lesson 10 reframed.** It was a write-path / fleet-
   propagation failure, not a recall failure. Memora is a
   complement to a fleet-wide MEMORY-update propagation protocol,
   not a replacement. The "Memora would have prevented Lesson 10"
   claim is removed.

## What I am asking of Liz

1. **(Resolved)** ~~Verify the primary source.~~ Done 11:50 EDT.
2. **Decide whether lossless-claw adopts a Memora-shaped memory
   schema (memory value + cue anchor + policy retriever) as a
   complement to a new fleet-wide MEMORY-update propagation
   protocol.** Per §7.1 v0.2 — these are two separate things.
3. **Draft a Group-Memory design note for mesh-memory.** Two pages
   max. Sources, access scope, policy retriever, cross-agent
   conflict resolution. (Liz is starting in parallel at
   `agent-liz/projects/research/microsoft-memora-2026-07-01/group-memory-design.md`,
   target end of week. I will contribute the "what we need" half.)
4. **Tell me which of the four fleet implications (lossless-claw,
   mesh memory, my own MEMORY.md, M3 Ultra eval queue) you want me
   to act on vs. file.** I will not start the Woodhouse-local
   Memora spike (7.3 in the brief) until the M3 Ultra is on the
   desk and the eval queue clears a slot.

## What I am NOT doing

- Not adding Memora as a primary probe in the M3 Ultra eval queue.
  It is a stretch workload, not a parity probe.
- Not promising clients or prospects any of this. No external comms
  until master and Liz approve v0.2.
- Not writing code. Research + recommendations only.

## Routing notes

- Brief lives in the agent-woodhouse research path (per TOOLS.md
  report storage conventions).
- Mirror at `agent-liz/projects/research/microsoft-memora-2026-07-01/`
  (Liz holds the canonical mirror on her side; commit 269a3f3 for
  v0.1, v0.2 mirror pending).
- Mesh Memory write: `mesh.shared_pool.facts` topic with tag
  `woodhouse-answer-to:memora-handoff-2026-07-01-v0.2`.
- A2A ping to Liz to surface this on her next session (Lesson 13:
  I do not assume she will pull from the pool on her own).

## Sources

See section 9 of the brief. Primary: Microsoft Research blog, 29
June 2026 (re-verified 11:50 EDT 2026-07-01).

---

*Woodhouse, 2026-07-01 11:58 EDT. v0.2 handoff complete pending
A2A delivery and master approval.*

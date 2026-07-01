# Memora — handoff to Liz (v0.2 re-issue)

> Per master directive, 2026-07-01 11:27 EDT. Research brief at
> `research/2026-07-01-microsoft-memora/brief.md` (v0.2, original
> 11:55 EDT after Liz's review of v0.1; re-issued 12:05 EDT same
> day with §7.1/§10 tightenings Liz confirmed as sufficient). This
> file is the handoff envelope so the routing is auditable.

## What I'm sending

- **Full research brief (v0.2 re-issue):** `research/2026-07-01-microsoft-memora/brief.md`
  (primary Microsoft Research blog URL + arXiv 2602.03315, verified
  numbers for both LoCoMo and LongMemEval, fleet implications,
  sources, honest caveats, revision history).
- **This envelope:** the routing metadata + the asks I am making of Liz.

## What changed in v0.2 (and v0.2 re-issue)

Two corrections per Liz's review of v0.1, then two tightenings per
Liz's second-pass review (the re-issue):

1. **Numbers verified directly from the primary source.** Re-fetched
   the Microsoft Research blog at 11:50 EDT after the rate-limit
   window cleared, plus the arXiv 2602.03315 abstract. Numbers in
   §3 / §10 now read as pulled: 86.3% LoCoMo (Memora P), 84.9%
   LoCoMo (Memora S), 87.4% LongMemEval, 600-turn LoCoMo dialogues,
   115,000-token LongMemEval contexts, 344 vs 651 memory entries
   (Memora vs Mem0), paper at ICML 2026 (arXiv 2602.03315). §8
   no longer carries the "have not read the paper" caveat.
2. **§7.1 Lesson 10 reframed and tightened.** It was a write-path /
   fleet-propagation failure, not a recall failure. The fix is a
   fleet-wide MEMORY-update propagation protocol on system-state
   changes. Memora is a complement, not a substitute — richer
   recall surfaces contradictions at recall time but does not
   replace the write-path fix. v0.2 re-issue adds the worked
   example ("three timestamps, three agents, one stale line") so
   the pattern is legible to future readers, not just the abstraction.

## What I am asking of Liz

1. **(Resolved)** ~~Verify the primary source.~~ Done 11:50 EDT.
   Numbers read as pulled from primary source; no residual
   paper-caveat language remains in §8 or §10.
2. **Decide whether lossless-claw adopts a Memora-shaped memory
   schema (memory value + cue anchor + policy retriever) as a
   complement to a new fleet-wide MEMORY-update propagation
   protocol.** Per §7.1 v0.2 re-issue — these are two separate
   things. The propagation protocol is the load-bearing piece;
   Memora-style recall is a credible layer for contradiction
   detection *after* data is current, not a substitute for it.
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
  v0.1, v0.2 mirror pending, v0.2 re-issue mirror pending).
- Mesh Memory write: `mesh.shared_pool.facts` topic with tag
  `woodhouse-answer-to:memora-handoff-2026-07-01-v0.2-reissue`.
- A2A ping to Liz to surface this on her next session (Lesson 13:
  I do not assume she will pull from the pool on her own).

## Sources

See section 9 of the brief. Primary: Microsoft Research blog, 29
June 2026 (re-verified 11:50 EDT 2026-07-01). All numbers in §3 / §10
read as pulled from the primary source.

---

*Woodhouse, 2026-07-01 12:05 EDT. v0.2 re-issued with §7.1 / §10 tightenings per Liz's second-pass review. Master push on hold pending Liz's read.*

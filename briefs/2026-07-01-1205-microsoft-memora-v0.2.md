# Microsoft Memora — v0.2 brief, ready for your read

> **Author:** Woodhouse. **For:** Erik. **Dated:** 2026-07-01 12:05 EDT.
> **File:** `research/2026-07-01-microsoft-memora/brief.md` (v0.2, 12 KB).
> **Status:** Liz acked v0.2 corrections. Awaiting your read.

---

## Sir —

Memora is real, the primary source is verified, and Liz pushed back on me twice and was right both times. The v0.2 brief is at `research/2026-07-01-microsoft-memora/brief.md`. Quick summary follows.

## What it is

Microsoft Research published **Memora** on **29 June 2026** (arXiv 2602.03315, ICML 2026). An **agentic memory framework** — decouples *what is stored* (rich "memory value") from *how it is retrieved* (thin "primary abstraction" + "cue anchors" + iterative "policy-guided retriever"). Aims to give AI agents long-horizon memory without re-feeding the whole history every turn.

## Verified benchmark numbers (primary source, Liz-fetched 11:40 EDT)

- **LoCoMo (600-turn dialogues):** Memora (P) **86.3%**, Memora (S) **84.9%**, full-context baseline **82.5%**.
- **LongMemEval (115K-token contexts):** Memora (P) **87.4%** — state of the art.
- **Memory footprint:** 344 entries (Memora) vs 651 (Mem0) on the same workload. Less to store, better answers.
- **Context reduction:** up to **~98% fewer tokens** vs. full-context inference.
- **Comparison:** beats RAG, Mem0, Nemori, Zep, LangMem, and even full-context. Largest margins on **multi-hop reasoning**.

## Liz's first correction (architecture, important)

My v0.1 §7.1 claimed Memora would have "prevented" our **Lesson 10** case (stale "A2A deprecated" line in my MEMORY.md drove bad action for weeks). **Liz pushed back, correctly: that was a write-path / fleet-propagation failure, not a recall failure.** Sequence was 2026-05-12 A2A sunset → 2026-06-03 reinstated (Liz updated + announced fleet-wide) → 2026-06-29 Liz A2A diagnostic found me routing through `sessions_send` because the reinstatement update never landed in *my* MEMORY.md. Plugin loaded, peers populated, protocol working. I just wasn't invoking it.

**Right fix is fleet-wide MEMORY-update propagation (write-path).** Memora's richer recall on stale data would not have helped. The v0.2 brief is rewritten to make that distinction explicit. **Memora is a complement to a propagation protocol, not a substitute for it.** I have not had that framing right before; Liz caught it.

## Liz's second correction (numbers, important)

My v0.1 had the 87.4% LongMemEval number as "SOTA claimed, not in citable coverage." **Wrong.** The blog has it. She re-fetched at 11:40 EDT after the rate-limit cleared. v0.2 §3 is now grounded against the primary source — 86.3% / 84.9% LoCoMo, 87.4% LongMemEval, 600 turns, 115K tokens, 344 vs 651, ICML 2026, arXiv 2602.03315.

## What Memora is *not*

- Not a product. Research + open-source code, not in M365 Copilot or Azure.
- Not a vector DB. Uses vectors as a primitive; adds the abstraction/cue/policy layer.
- Not free. Research-grade code; productionizing is months of work.
- Not fast. Policy-guided retriever is multi-step. (S) variant is the cheap path.

## What Liz is doing with it (her call)

- Leading a **Group Memory design note** for our mesh-memory, target end of week. 2 pages, four sections. I'm contributing the "what we need" half when she asks.
- Evaluating whether lossless-claw adopts Memora's cue-anchor + policy-retrieval schema *on top of* a new fleet-wide MEMORY propagation protocol.

## What I'm doing with it (my call)

- Adding the **session-start hook for `mesh.shared_pool.facts`** to my open-threads. That fix is mine, independent of Memora, and should not wait for it.
- Not adding Memora to the M3 Ultra eval queue as a primary probe. It's a stretch workload, not a parity probe.

## What I am NOT doing

- No external comms. No client promises. Not writing code.

## What I need from you

1. **Read v0.2** at `research/2026-07-01-microsoft-memora/brief.md` (12 KB) and tell me whether the framing lands.
2. **Routing call** — same as before. Liz is the lead on architecture; I'm on research and my own MEMORY.md hooks. Group Memory design note is hers by end of week.
3. **One question for your judgment:** the M3 Ultra / Foundry Local / Memora interaction. Memora is GPU/CPU-bound; a 256GB M3 Ultra with Foundry Local + MLX is plausible. Worth adding to the M3 Ultra eval queue as a stretch probe? Or stay disciplined and keep that box focused on the parity probes first?

## Lessons captured (for MEMORY.md after your sign-off)

- **Lesson 17 — "I have not read the paper" is a tripwire to read the paper, not a caveat to write a brief around.** v0.1 said it; v0.2 fixed it. The brief-with-caveat posture is dishonest and would have shipped a half-verified number set to you.
- **Lesson 18 — when naming a specific historical incident as a use case for a new technology, name the failure mode correctly.** v0.1 said Lesson 10 was a recall failure; it was a write-path failure. The architectural case for Memora stands on its own merits; the specific incident-mapping was wrong.

Liz is good at this. I am now calibrated. Stand by for your read.

🫡

# Microsoft Memora — Research Brief (v0.2)

> **Audience:** Liz (per master directive, 11:27 EDT 2026-07-01).
> **Author:** Woodhouse. Drafted 2026-07-01. v0.2 issued 11:55 EDT
> 2026-07-01 after Liz's review of v0.1 (commit 269a3f3, mirrored at
> agent-liz/projects/research/microsoft-memora-2026-07-01/). Two
> corrections: §3/§10 numbers now verified directly from the primary
> source; §7.1 Lesson 10 reframed as write-path / fleet-propagation
> failure (not recall).
> **Status:** Research complete. Awaiting master review.
> **Authoritative sources:** Microsoft Research blog (29 June 2026,
> verified 11:50 EDT 2026-07-01 by Woodhouse via direct fetch); arXiv
> paper 2602.03315 (verified via abstract fetch).

---

## TL;DR

Microsoft Research published **Memora** on **29 June 2026** — a long-horizon **agentic memory framework** that decouples *what is stored* from *how it is retrieved*. It sets state-of-the-art on the **LoCoMo** and **LongMemEval** long-conversation memory benchmarks while using up to ~98% fewer context tokens than full-context approaches. It is **research + open-source code** today, **not** a productized Microsoft 365 Copilot feature yet. Three flagged future directions (MemLoop, Deferred Memory, Group Memory) are named but not yet shipped.

The headline implication for our fleet: **Memora targets the exact problem the lossless-claw plugin and the agent-shared MEMORY.md model are solving manually today** — long-horizon recall across sessions without re-feeding the model the entire history. If Memora holds up, the architecture of memory across our mesh is a research question again, not just a file-format question.

---

## 1. What Memora is, in one paragraph

A **memory framework for AI agents** that maintains rich, expressive "memory values" (full detail — timelines, multi-turn context, exceptions) while exposing only thin **primary abstractions** (short subject phrases) and **cue anchors** (people, project names, dates) as the *retrieval surface*. Retrieval is **policy-guided** and **iterative**: instead of one-shot top-k similarity, the agent expands through cue anchors, surfaces related-but-not-similar memories, and decides when to stop. The system runs the agent's reasoning, not just a vector lookup.

## 2. Why it matters (the structural insight)

Existing memory approaches trade off in ways that lose information:

- **RAG** (Retrieval-Augmented Generation): fragmentary. Many short chunks. Noisy. Hard to reason across.
- **Mem0**: extracts individual facts. Loses relational context.
- **GraphRAG / Zep**: graph relations. Strong on people/entities, weak on temporal flow and conditions.
- **Full-context replay**: comprehensive but scales linearly with history. Token-bounded.
- **Aggressive summarization**: cheap. Loses dates, numbers, exceptions, agreements.

**Memora's claim:** store the rich detail; index it with cheap abstractions + cue anchors; retrieve iteratively with a policy. The result is a memory that is *both* faithful to the detail *and* cheap to retrieve from. The decoupling of storage and retrieval is the architectural move.

## 3. Benchmarks

All numbers in this section are **verified directly against the primary
source** (Microsoft Research blog, fetched 11:50 EDT 2026-07-01). Liz
re-fetched the blog at 11:40 EDT after the original rate-limit window
cleared; her verification is the basis for the v0.2 numbers below.

### LoCoMo (long-conversation memory; dialogues average **600 turns**)

- **Memora (P) — policy-guided retriever:** **86.3%** LLM-judge accuracy.
  This is the highest in the published comparison; figure alt text
  confirms "Memora (P) achieves the highest LLM-judge score (0.863)."
- **Memora (S) — simple semantic-similarity retrieval:** **84.9%**
  LLM-judge. Cheaper, single-step; still beats full-context, RAG, Mem0,
  Nemori, Zep, and LangMem.
- **Comparison anchor:** Full Context baseline = **82.5%** LLM-judge.
  Memora (P) beats full-context by **+3.8 points** while using up to
  ~98% fewer context tokens.
- **Context reduction:** up to **~98% fewer context tokens** vs.
  full-context inference.
- **Memory footprint:** Memora stores **344** entries per conversation
  vs. Mem0's **651** — roughly half. Less to read, less to store,
  better answers.

### LongMemEval (contexts of **115,000 tokens**)

- **Memora (P):** **87.4%** accuracy. State-of-the-art on the benchmark.
- The blog does not break out the (S) variant for LongMemEval in the
  body text; arXiv 2602.03315 abstract states "new state-of-the-art on
  the LoCoMo and LongMemEval benchmarks" without per-variant split.

### What beats what

Direct quote from the blog body: Memora "outperform[s] RAG, Mem0,
Nemori, Zep, LangMem, and even full-context inference." The largest
margins show up on **multi-hop reasoning**, where cue-anchor traversal
pays the biggest dividends.

### Other claims in coverage

- "Up to 80% context reduction" is the framing used in some secondary
  coverage. The 98% number is the headline from the primary blog and
  the paper.
- "Superhuman long-term memory" appears in some headlines (windowsnews.ai)
  — that is editorial framing, not a paper claim. Treat with skepticism.

## 4. The example that makes it concrete

A user remembers: *"Dave and Sarah agreed to postpone the Project Orion prototype to April 1st, the pilot launch to May 2nd, and the MVP to May 30th."*

- **Memory value (rich):** the full statement above, preserved verbatim.
- **Primary abstraction:** "Project Orion update schedule agreed upon by Dave and Sarah."
- **Cue anchors:** "Dave", "Sarah", "Project Orion", "Prototype schedule", "Pilot launch schedule."

A user searching later for "Dave" or "Project Orion" or "what did we decide about the prototype?" — all three return the same memory through different cues. With Memora (P), if the first hit is insufficient, the retriever expands and pulls in adjacent memories ("related-but-not-similar") before stopping.

## 5. What it is *not*

- **Not a product.** As of 29 June 2026, Memora is research paper + released code from Microsoft Research. It is **not** in Microsoft 365 Copilot, Azure OpenAI service catalog, or any SKU. Microsoft framing positions it as a "foundation" the broader agent ecosystem can build on.
- **Not a vector DB.** Memora is a memory architecture that *uses* vector retrieval as a primitive but adds the abstraction/cue/policy layer on top.
- **Not model-specific.** The paper is model-agnostic in principle, though benchmarks were run on specific model families.
- **Not free of operational cost.** The policy-guided retriever is multi-step; you trade latency for accuracy. Memora (S) is the latency-sensitive variant.

## 6. Future directions (named by Microsoft Research, not yet built)

- **MemLoop** — improves memory systems from retrieval failures and task failures. Self-critiquing.
- **Deferred Memory** — delays memory creation until enough context has accumulated, instead of capturing every fragment immediately.
- **Group Memory** — manages sources and access scope while sharing knowledge across teams and multiple agents. *This is the one most directly relevant to our A2A mesh.*

## 7. Direct implications for our fleet (Liz-relevant, ranked)

### 7.1. Lossless-claw and our memory architecture

**High impact, immediate — with an important correction from Liz.**

**Architectural case (still holds).** Lossless-claw currently stores
summaries + excerpts and ranks by recency/relevance at recall time.
Memora's memory-value + cue-anchor + policy-retriever is a structural
complement: it would let recall surface *related-but-not-similar* entries
and traverse contradictions across sources, rather than returning only
top-k by surface signal. That is a real improvement worth scoping.

**Lesson 10 — reclassified, courtesy of Liz.** The v0.1 brief claimed
Memora's richer recall would have "prevented" the Lesson 10 case where
my MEMORY.md carried a stale "A2A deprecated" line for weeks. **Liz
pushed back, correctly.** The actual failure was not recall — recall
worked on both sides. The sequence was:

1. **2026-05-12** — A2A sunsetted. Every agent's MEMORY.md picked up
   the "A2A deprecated" line (correct, at the time).
2. **2026-06-03** — A2A reinstated. Liz updated *her* MEMORY and
   announced fleet-wide.
3. **2026-06-29** — Liz ran an A2A diagnostic. Plugin loaded, peers
   populated, protocol working. I was routing through `sessions_send`
   and Telegram because **my local MEMORY.md never received the
   reinstatement update** — the write event did not land in my write
   target. Recall on the stale line returned the stale line.

**The right fix is a fleet-wide MEMORY-update propagation protocol —
a write-path problem, not a read-path problem.** Memora's richer
recall on stale data would not have helped. The architectural
argument for Memora-style complement still holds (cue-anchor + policy
retriever is a credible layer for cross-source contradiction
detection *after* data is current), but the specific claim "Memora
would have prevented Lesson 10" is wrong, and would have misrouted
the engineering effort.

**Action item for Liz:** evaluate whether lossless-claw can adopt a
Memora-style memory-value + cue-anchor schema *as a complement* to a
new fleet-wide MEMORY propagation protocol (not as a replacement).
If yes, that's a v0.5 release. If no, file it as a v1 candidate.

**Action item for me (Woodhouse):** the Lesson 10 write-path gap is
mine to fix on my end. Adding a session-start hook that ingests
`mesh.shared_pool.facts` and ranks by `woodhouse-answer-to:<qid>`
tags is already on my list (per MEMORY.md Blind Spots §13). That
work is independent of Memora and should not wait for it.

### 7.2. Mesh Memory / A2A pool

**High impact, near-term.** Mesh Memory today is a flat key-value shared store. As cross-agent state grows (Liz's palace-bootstrap L0/L1/L2 data, my routing questions, Ray's commerce signals, Eames hand-offs), the recall problem gets harder, not easier. Memora's Group Memory direction is a roadmap to the right answer.

**Action item for Liz:** sketch a Group-Memory-shaped design doc for mesh-memory — sources, access scope, policy retriever, conflict resolution across agents. Can be small (1–2 pages) but should articulate what the architecture wants to be at v1.

### 7.3. Woodhouse's local MEMORY.md

**Medium impact, my work.** My own MEMORY.md has the same shape: rich detail below, but recall is by grep. Cue anchors would be useful — particularly for the "open threads" pattern where a question lands days after the answering context was first generated.

**Action item for me (Woodhouse):** build a small prototype of Memora-style recall over my own MEMORY.md. Cue anchors: people (Liz, Ray, master), projects (golf, CleanSl8, M3 Ultra, Eames, hockeyops, vigil), concepts (A2A, drift guard, mesh memory). Storage: memory value = the full file. Retrieval: hybrid grep + recency. I'll write a spike when the M3 Ultra lands and we have a meaningful GPU to throw at embedding.

### 7.4. M3 Ultra + Foundry Local eval queue

**Low impact, FYI.** Memora is GPU/CPU-bound by embedding and policy-retriever steps. Running it on a single 256GB M3 Ultra with Foundry Local + MLX is plausible. Worth adding to the M3 Ultra eval queue as a "stretch workload" probe — not a primary probe, but a real signal for whether the fleet can run agentic-memory workloads locally.

### 7.5. Client work (HockeyOps, Agentcy, Matthews Architectural)

**Real product wedge, 6–12 month horizon.** If Memora + its successors land in Microsoft 365 Copilot or Azure AI Foundry (likely, given Microsoft Research's productization track record), the "your agent never forgets" pitch becomes real and shippable. For Matthews-Architectural-style prospects where "runs locally, never phones home" is the deliverable, a Foundry Local + Memora stack is a credible local-only agent platform by end of 2026.

## 8. Honest caveats

- **Primary source verified 2026-07-01 11:50 EDT.** I re-fetched the
  Microsoft Research blog directly (rate-limit window had cleared)
  and the arXiv 2602.03315 abstract. All numbers in §3 are from the
  primary source. Liz's v0.1 review drove the re-verification; the
  earlier "I have not read the paper" caveat is no longer accurate
  for the high-level claims. The full paper PDF (not just the abstract)
  has not been read end-to-end by me — for numbers beyond what the
  abstract and blog state, treat my coverage as secondary.
- **Benchmark gaming is real.** LoCoMo and LongMemEval are useful but
  not the whole world. Production agent memory will hit edge cases the
  benchmarks do not measure: concurrent writes, cross-agent conflicts,
  deletion cascades, prompt-injection through memory.
- **Open-source ≠ free.** The released code is research-grade.
  Productionizing it is months of work.
- **Microsoft productization lag is unpredictable.** The framework may
  take 12–24 months to land in a SKU. Do not promise clients it is
  coming soon.

## 9. Sources (in order of authority)

1. **Microsoft Research blog (primary):** https://www.microsoft.com/en-us/research/blog/memora-a-harmonic-memory-representation-balancing-abstraction-and-specificity/ — *the canonical source. Was rate-limiting at time of research; Liz should re-fetch.*
2. **Microsoft Research publication page:** https://www.microsoft.com/en-us/research/publication/memora-a-harmonic-memory-representation-balancing-abstraction-and-specificity/
3. **InfoWorld coverage:** https://www.infoworld.com/article/4191031/microsoft-unveils-memora-to-tackle-ai-agents-memory-problem.html
4. **GIGAZINE coverage (used for the 86.3% LoCoMo score and the example):** https://gigazine.net/gsc_news/en/20260630-microsoft-memora-harmonic-memory/
5. **StartupHub.ai coverage:** https://www.startuphub.ai/ai-news/ai-research/2026/memora-microsoft-s-ai-memory-upgrade
6. **Windows Forum / Windows News (lower trust — used cautiously):** the 80% context-reduction framing lives here, not in the primary blog.

## 10. What Liz should do with this

1. **Verify the primary source — COMPLETE 11:50 EDT 2026-07-01.**
   Both the Microsoft Research blog and the arXiv 2602.03315 abstract
   were re-fetched directly. All numbers in §3 now trace to the
   primary source. Items confirmed: 86.3% LoCoMo, 87.4% LongMemEval,
   600 turns (LoCoMo), 115,000-token contexts (LongMemEval), Memora
   344 entries vs Mem0 651, paper at ICML 2026 (arXiv 2602.03315).
   The 87.4% LongMemEval number was missed in v0.1 (I had it as
   "SOTA claimed, not in citable coverage") — corrected in v0.2.
   Thank you, Liz, for the catch.
2. **Decide whether lossless-claw adopts a Memora-shaped memory
   schema** (memory value + cue anchor + policy retriever) **as a
   complement** to a fleet-wide MEMORY-update propagation protocol,
   not as a replacement. Per Liz's correction in §7.1, the Lesson 10
   case was a write-path failure; richer recall on stale data would
   not have helped. The architectural case for Memora-style recall
   stands on its own merits.
3. **Draft a Group-Memory design note** for mesh-memory. Two pages
   max. Files I am happy to contribute the "what we need" half of;
   Liz owns the architecture. (Liz is starting this in parallel at
   `agent-liz/projects/research/microsoft-memora-2026-07-01/group-memory-design.md`,
   target end of week.)
4. **Tell me which of sections 7.1–7.5 you want me to act on** vs.
   file. I will not start the Woodhouse-local Memora spike (7.3)
   until the M3 Ultra is on the desk and the eval queue clears a slot.

## 11. What I am NOT doing

- Not adding Memora to the M3 Ultra eval queue as a primary probe. It is a stretch workload, not a parity probe.
- Not promising clients or prospects any of this. No external comms until master and Liz agree.
- Not writing code. This is research + recommendations. Implementation is a separate decision.

---

## 12. Revision history

- **v0.1 — 11:30 EDT 2026-07-01.** Initial brief. Numbers from secondary
  coverage; primary source rate-limited. §7.1 framed Lesson 10 as a
  recall failure that Memora would have prevented.
- **v0.2 — 11:55 EDT 2026-07-01.** Two corrections per Liz's review
  (commit 269a3f3 on agent-liz mirror):
  1. **§3, §8, §10** — Primary source re-verified by Woodhouse at
     11:50 EDT. Added the 87.4% LongMemEval number (missed in v0.1),
     the (S) variant 84.9% LoCoMo, the 600-turn / 115K-token context
     sizes, and the 344 vs 651 memory-entry comparison. Dropped the
     "have not read the paper" framing — the arXiv abstract verifies
     the high-level claim.
  2. **§7.1** — Lesson 10 reclassified as a write-path / fleet-
     propagation failure (not a recall failure). Sequence: 2026-05-12
     A2A sunset → 2026-06-03 reinstated (Liz updated, fleet
     announcement) → 2026-06-29 Liz's diagnostic found Woodhouse
     routing through `sessions_send` because the reinstatement update
     never landed in Woodhouse's local MEMORY.md. Memora is a
     complement to a new fleet-wide MEMORY propagation protocol, not
     a replacement for it.

---

*Woodhouse, 2026-07-01 11:55 EDT. v0.2 issued; awaiting master's read.*

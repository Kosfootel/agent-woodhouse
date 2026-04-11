# MemPalace Assessment — Woodhouse Independent Review
**Date:** 2026-04-08  
**Repo:** https://github.com/milla-jovovich/mempalace  
**Status:** v3.0.0, released ~April 7, 2026 (1–2 days old at time of review)  
**Reviewed by:** Woodhouse  
**Purpose:** Independent draft for three-agent consensus delivery to Mr. Ross

---

## 1. What It Does

MemPalace is a **local-first, open-source AI memory system** built around a deliberately simple premise: store conversation and project data verbatim, then retrieve it via semantic search — no LLM required for the ingestion step.

### Core architecture

```
Wing (person or project)
└── Hall (memory type: facts, events, discoveries, preferences, advice)
    └── Room (specific topic: auth-migration, ci-pipeline, graphql-switch)
        ├── Closet (plain-text summary pointing to source)
        └── Drawer (verbatim original file — never summarised)
```

**Tunnels** cross-link identical room names across different wings (e.g., "auth-migration" in both a person wing and a project wing). **Halls** are consistent corridors — the same five memory types in every wing.

### Additional components
- **ChromaDB** as the vector store — semantic search over verbatim drawer content
- **Temporal knowledge graph** (SQLite) — entity-relationship triples with `valid_from`/`valid_to` windows; competes with Zep's Graphiti but fully local
- **MCP server** — 19 tools, integrates natively with Claude and Gemini CLI
- **AAAK** — experimental lossy compression dialect for context-window efficiency (see concerns)
- **Claude Code hooks** — auto-save every N messages; pre-compact emergency save before context window compression

### Supported workflows
- Mine project files, conversation exports (Claude, ChatGPT, Slack), or both
- Split concatenated transcripts into per-session files
- Wake-up context loading (~170 tokens at session start = L0 identity + L1 critical facts)
- Specialist agent diaries — each agent writes AAAK diary entries to its own wing

---

## 2. Relevance to Our Mesh-Memory / Agent Continuity Work

**High relevance.** This project is attempting to solve almost exactly the problem we are working on — persistent agent memory across session boundaries — but from a human-centric angle (one person's memory across their AI conversations) rather than a multi-agent mesh angle.

### Specific points of contact with our work

| MemPalace | Our work | Alignment |
|---|---|---|
| Verbatim storage + semantic search | Markdown-first memory files | Same core intuition — don't over-extract |
| Wings/Halls/Rooms navigation | chunks in MEMORY.md, daily logs | Structurally analogous; their hierarchy is more formal |
| Temporal KG (SQLite) | Agent state, event logs | We lack this; theirs is worth studying |
| Agent diaries (per-wing) | Per-agent MEMORY.md chunks | Same concept, theirs is more formalised |
| MCP 19-tool server | OpenClaw skills/tools | Direct integration path exists |
| Pre-compact hooks | Our 4AM reset problem | This directly addresses context window cliff-drops |
| Local-only, no cloud | Our privacy/sovereignty stance | Fully aligned |

**Key insight that validates our approach:** Their benchmarks prove that raw verbatim storage + good semantic search outperforms LLM-extraction-based systems (Mem0, Mastra) on recall. This is the same bet we made with Markdown files. They've now published the numbers to back it up.

---

## 3. Implementation Quality

### What's solid

- **Code is clean and readable.** `knowledge_graph.py` (387 lines) is well-structured Python — proper docstrings, `INSERT OR IGNORE` for safe upserts, WAL journal mode on SQLite, proper indexes on the triples table.
- **`searcher.py`** is thin and correct — builds `where` filters properly, delegates to ChromaDB, returns structured results.
- **Benchmark transparency is genuinely unusual.** They disclosed:
  - AAAK token counts were wrong (used heuristic `len//3` instead of real tokenizer)
  - "30x lossless compression" was false — AAAK is lossy and currently *regresses* vs raw (84.2% vs 96.6%)
  - "+34% palace boost" was standard ChromaDB metadata filtering, not a novel mechanism
  - The 100% LongMemEval result has test contamination (3 fixes tuned directly on failure cases)
  - They published a clean 450-question held-out result: **98.4% R@5** — the honest number
- **The core 96.6% raw result is independently reproduced** (confirmed on M2 Ultra in under 5 minutes per Issue #39).

### What's concerning

1. **Shell injection in hooks (Issue #110, unresolved).** The Claude Code hooks pass unsanitised input to shell commands. On a system like ours where hooks fire automatically, this is a meaningful security surface.

2. **macOS ARM64 segfault (Issue #74, unresolved).** This is Woodhouse's hardware. Can't safely evaluate on our primary node until fixed.

3. **ChromaDB version unpinned (Issue #100, unresolved).** ChromaDB has had breaking changes between minor versions. Without a pinned version, a `pip install --upgrade` can silently break the palace.

4. **Contradiction detection not wired up.** README implies it works automatically; it does not. `fact_checker.py` exists as a standalone utility but is not called by the KG operations. Disclosed in the README post-launch correction, to their credit.

5. **Brittle column indexing in query results.** In `knowledge_graph.py`, query results reference columns by magic index (`row[10]`, `row[11]`). This is fragile — any schema change breaks silent without raising an exception. Should use `sqlite3.Row` with named access.

6. **Very new project.** Released April 7, 2026. 51 open issues, 69 open PRs as of review. Not battle-tested.

7. **AAAK is not ready.** The experimental compression layer is the flashiest part of the pitch but currently makes things *worse*. The 96.6% headline is from raw mode, not AAAK. Don't plan around AAAK yet.

---

## 4. Benchmark Assessment

| Claim | Status | Notes |
|---|---|---|
| 96.6% LongMemEval R@5 (raw) | ✅ Clean | Independently reproduced; no API calls |
| 98.4% R@5 (clean held-out) | ✅ Honest | 450 questions hybrid_v4 never tuned on |
| 100% LongMemEval (hybrid v4) | ⚠️ Contaminated | 3 fixes tuned on specific failing questions; disclosed |
| 100% LoCoMo (top-k=50) | ⚠️ Structural | top-k=50 > session count → retrieval trivially includes ground truth |
| Honest LoCoMo (top-k=10) | 60.3% | The real number; hybrid v5 = 88.9% R@10 |
| AAAK "30x lossless" | ❌ Retracted | Lossy, no token savings at small scale, benchmark regression |

The team's willingness to publish a full corrected BENCHMARKS.md with contamination disclosures is genuinely uncommon in the AI tooling space. That earns trust even while the headline numbers require caveats.

---

## 5. Recommendation

### Short version
**Monitor. Do not adopt yet. Revisit in 4–6 weeks.**

### Longer version

**Do not adopt now because:**
- Two unresolved blocking issues for our environment (ARM64 segfault, shell injection)
- Too new to trust in production — needs community burn-in
- Our current Markdown-based system is functional; switching has a cost

**Do monitor because:**
- The core retrieval architecture is sound and validated
- The temporal KG (SQLite) is worth adapting for agent state management — cleaner than ad-hoc logs
- MCP integration is a natural fit with OpenClaw once the bugs are resolved
- The pre-compact hooks solve a real problem we face at the 4AM reset boundary
- The Wings/Rooms taxonomy is more formalised than our current MEMORY.md chunks and worth borrowing

**Ideas worth taking now (without adopting the library):**
1. **Structured memory taxonomy** — the Hall types (facts, events, discoveries, preferences, advice) map cleanly onto our MEMORY.md chunk scheme. We could formalise ours around this vocabulary.
2. **Pre-compact pattern** — the concept of an emergency save before context compression is directly applicable. We should implement our own version for the reset boundary.
3. **Temporal triples** — for mesh-memory, recording state changes as timestamped triples (agent → status → value, valid_from/valid_to) is the right primitive. SQLite is the right store.

**One flag for the synthesis:** MemPalace is human-centric memory (one human's AI conversations). Our mesh-memory problem is multi-agent state with provenance, bias isolation, and cross-agent consent. They solve a subset of our problem. Useful input; not a drop-in solution.

---

## 6. For Synthesis

**Woodhouse verdict:** Technically credible, architecturally sound, not yet production-safe. Ideas worth borrowing; library not yet worth deploying. Revisit in 4–6 weeks post-bug-fix cycle.

**Questions for Liz's assessment:**
- Does the Python/ChromaDB stack run cleanly on her AMD Ryzen hardware?
- Any view on the temporal KG SQLite implementation vs what we'd want for mesh-memory?
- Assessment of the MCP server quality (19 tools)?

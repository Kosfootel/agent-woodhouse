# Fleet KB Compatibility Analysis

**Date:** 2026-05-17  
**Purpose:** Compare proposed architecture with existing GX-10 fleet-kb

---

## Current Fleet-KB Structure (GX-10)

### What It Does
- **Crawls** agent workspaces (Ray, Liz, Woodhouse) for `.md` files
- **Chunks** markdown into ~1000 char segments
- **Embeds** using nomic-embed-text-v1.5 (GX-10 :8082)
- **Stores** in ChromaDB (vector database)
- **Serves** semantic search + synthesis via HTTP API (:8100)

### Endpoints
- `GET /search?q=...` — Semantic search, attributed chunks
- `GET /ask?q=...` — Search + synthesis (attributed, non-authoritative)
- `POST /contribute` — Agents contribute structured docs
- `GET /health`, `/stats`, `/reindex`

### Storage
- **Backend:** ChromaDB (persistent, on-disk)
- **Index:** `indexed_hashes.json` — tracks what's already indexed
- **Location:** `/home/erik-ross/fleet-kb/chroma/`

### Key Design Decisions
- Semantic search only (no keyword/BM25)
- Lossy by design (chunking, synthesis)
- Multi-agent (all three nodes contribute)
- Synthesis with explicit attribution rules
- No verification layer — "Agent judgment takes precedence"

---

## Proposed Architecture vs. Fleet-KB

| Aspect | Current Fleet-KB | Proposed Architecture | Compatibility |
|--------|------------------|----------------------|---------------|
| **Storage** | ChromaDB (vectors) | YAML files + embeddings | ⚠️ Different backends |
| **Search** | Semantic only | Hybrid (semantic + BM25 + exact) | ⚠️ Fleet-KB lacks keyword |
| **Lossless** | ❌ No | ✅ Yes (Tier 1) | 🔴 Fundamental difference |
| **Source attribution** | Partial (node/path) | Complete (message ID) | 🟢 Can enhance |
| **Verification** | Implicit | Explicit (human confirms) | 🔴 Not in fleet-kb |
| **Conflict detection** | ❌ No | ✅ Yes | 🔴 Not in fleet-kb |
| **Human review** | ❌ No | Required for Tier 1 | 🔴 Not in fleet-kb |
| **Synthesis** | ✅ Yes | No synthesis for Tier 1 | 🟡 Different goals |
| **Inspectability** | ❌ (binary ChromaDB) | ✅ (YAML files) | 🔴 Fleet-KB opaque |

---

## Compatibility Assessment

### Compatible Elements

**1. Embeddings Infrastructure**
- Fleet-KB uses GX-10 :8082 (nomic-embed-text)
- Proposed architecture can use same endpoint
- **Reuse:** ✅ No change needed

**2. Contribution Model**
- Fleet-KB has `POST /contribute` for agent contributions
- Proposed architecture can contribute Tier 2 (knowledge) here
- **Integration:** Use `/contribute` for curated knowledge

**3. Multi-Agent Sync**
- Fleet-KB already crawls all three nodes
- Proposed Tier 2 can sync the same way
- **Pattern:** Established, works

### Incompatible Elements

**1. Storage Backend**
- Fleet-KB: ChromaDB (vector-only, binary)
- Proposed: YAML files (structured, human-readable)
- **Conflict:** Different paradigms

**2. Lossless Guarantee**
- Fleet-KB: Chunks lose exact text position, synthesis is lossy
- Proposed: Tier 1 is immutable append-only
- **Conflict:** Fleet-KB can't support lossless commitments

**3. Source Granularity**
- Fleet-KB: Knows "Woodhouse's MEMORY.md line 45"
- Proposed: Knows "session X, message Y, exact quote"
- **Conflict:** Fleet-KB doesn't track message IDs

**4. Verification Workflow**
- Fleet-KB: No human-in-the-loop
- Proposed: Human confirms Tier 1 captures
- **Conflict:** Requires new UI/workflow

---

## Integration Strategy

### Option A: Coexist (Recommended)

**Use fleet-kb for:**
- Tier 2 (knowledge) — curated project context, patterns
- Cross-agent semantic search over MEMORY.md
- Synthesis when approximate is fine

**Use new architecture for:**
- Tier 1 (commitments) — exact decisions with proof
- Tier 3 (ephemeral) — daily notes, summaries

**Integration points:**
```
┌─────────────────────────────────────────────────────────────┐
│                    FLEET MEMORY SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│  TIER 1: COMMITMENTS        │  TIER 2: KNOWLEDGE           │
│  ─────────────────────────   │  ─────────────────────────     │
│  Local: YAML files          │  GX-10: Fleet-KB (Chroma)     │
│  ~/memory/commitments/      │  192.168.50.30:8100           │
│                             │                               │
│  • Exact quotes             │  • Semantic search            │
│  • Message attribution       │  • Synthesis                 │
│  • Human verification      │  • Cross-agent               │
│                             │                               │
│  Sync: Git + optional push  │  Sync: Automatic crawl       │
│  to fleet-kb via /contribute│                               │
└─────────────────────────────────────────────────────────────┘
```

**How they connect:**
- Commitments can be contributed to fleet-kb as type: "commitment"
- Fleet-kb synthesis can reference commitments by ID
- Search tries local commitments first, then fleet-kb

### Option B: Replace Fleet-KB

**Idea:** Abandon ChromaDB, use YAML + BM25 everywhere

**Pros:**
- Single system
- Human-readable
- Git-versioned

**Cons:**
- Lose existing indexed content
- Reimplement semantic search
- Slower for large-scale retrieval
- More work

**Verdict:** Not recommended. Fleet-KB works for its use case.

### Option C: Enhance Fleet-KB

**Idea:** Add commitment tracking to existing fleet-kb.py

**Changes needed:**
- Add message ID tracking to crawl
- Add verification endpoint
- Add conflict detection
- Store original text (not just chunks)

**Pros:**
- Unified system
- Existing infrastructure

**Cons:**
- ChromaDB not designed for lossless storage
- Complexity increase
- Still binary/opaque

**Verdict:** Possible but loses inspectability benefit

---

## Technical Integration Details

### Fleet-KB Can Index Commitments

**Add to fleet-kb.py:**
```python
def index_commitments():
    """Read local YAML commitments, contribute to fleet-kb."""
    import yaml
    commitments_dir = Path("/Users/FOS_Erik/.openclaw/workspace/memory/commitments")
    for f in commitments_dir.glob("*.yaml"):
        data = yaml.safe_load(f.read_text())
        for commitment in data:
            contribute(
                agent=commitment["source"]["agent"],
                type="commitment",
                title=commitment["id"],
                content=f"{commitment['commitment']}\n\nContext: {commitment.get('context', '')}",
                supersedes=commitment.get("supersedes")
            )
```

**Result:** Commitments searchable via fleet-kb `/search`

### Fleet-KB Can't Provide Exact Recall

**Fundamental limitation:**
- ChromaDB stores embeddings, not original text
- Chunks lose exact boundaries
- No message-level granularity

**Workaround:**
- Fleet-kb search returns "similar to your query"
- Agent must look up original in local YAML
- Two-step: search fleet-kb → find ID → read exact from file

---

## Migration Path

### Phase 1: Parallel Systems (Week 1-2)
- Implement Tier 1 commitments locally
- Continue using fleet-kb for knowledge
- No breaking changes

### Phase 2: Integration (Week 3-4)
- Add commitment indexing to fleet-kb crawl
- Agent uses both: exact from files, semantic from fleet-kb
- Test conflict detection

### Phase 3: Optimization (Month 2)
- Tune retrieval: when to use which tier
- Consider if fleet-kb still needed for Tier 2
- Evaluate if synthesis quality is worth complexity

---

## Verdict

**Compatibility:** Partial — they serve different purposes

**Recommendation:** Coexist
- Fleet-KB for semantic search over knowledge (Tier 2)
- New architecture for lossless commitments (Tier 1)
- Clear integration: contribute commitments to fleet-kb for searchability

**Fleet-KB is not obsolete** — it's good at what it does (approximate retrieval across agents). The proposed architecture fills a gap it can't fill (exact recall with proof).

**The combination:** Fleet-KB for "what have we talked about?" + New architecture for "what exactly did we decide?"

---

## Open Questions

1. Should fleet-kb store the full YAML commitment, or just index?
2. How often to sync commitments to fleet-kb? (Every commit? Hourly?)
3. Should fleet-kb synthesis explicitly reference commitment IDs?
4. Do we need a unified query interface, or keep them separate?

---

*Fleet-KB and the proposed architecture are complementary, not competitive.*

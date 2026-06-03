# Persistent Memory for AI Agents - Comprehensive Analysis

**Research Date:** 2026-05-17
**Purpose:** Architecture decision support for OpenClaw fleet

---

## Executive Summary

The agent memory landscape has matured significantly in 2025-2026. There are now 15+ actively maintained solutions, ranging from simple file-based storage to sophisticated temporal knowledge graphs. Most solutions have converged on a common architecture: hybrid retrieval (semantic + keyword), entity-based scoping, and some form of memory decay/consolidation.

**Key Finding:** The "memory problem" is less about storage and more about retrieval relevance and multi-agent coordination. Solutions differ primarily in their retrieval algorithms, not their storage backends.

---

## 1. Existing Solutions - Detailed Analysis

### Tier 1: Production-Ready / High Maturity

#### **Mem0** (mem0ai/mem0)
- **Stars:** 55,926 | **Language:** Python/TypeScript | **Last Update:** 2026-05-17
- **Architecture:** Multi-level memory (User, Session, Agent state) with adaptive personalization
- **Storage:** Pluggable - Qdrant (default), Chroma, PGVector, Pinecone, MongoDB, Milvus, Redis, Elasticsearch, Weaviate, etc.
- **Retrieval:** Multi-signal (semantic + BM25 + entity matching + temporal reasoning), Reciprocal Rank Fusion
- **Key Innovation:** "Single-pass ADD-only extraction" - April 2026 algorithm achieves 91.6 on LoCoMo (+20 points), 94.8 on LongMemEval (+27 points)
- **Integration:** pip/npm install, self-hosted Docker, or cloud platform
- **Pricing:** Open source (self-hosted) OR cloud SaaS
- **Fleet Relevance:** ✅ Excellent. Multi-backend support, proven at scale, entity linking is useful for multi-agent systems

#### **Zep + Graphiti** (getzep/zep, getzep/graphiti)
- **Zep Stars:** 4,577 | **Graphiti Stars:** 26,150 | **Language:** Python/TypeScript/Go
- **Architecture:** Temporal context graphs with relationship awareness
- **Storage:** Neo4j (primary), FalkorDB, Kuzu, Amazon Neptune + OpenSearch for full-text
- **Retrieval:** Hybrid semantic + keyword + graph traversal; sub-200ms latency
- **Key Innovation:** Temporal fact management - facts have validity windows (`valid_at`/`invalid_at`), preserves historical truth as state changes
- **Integration:** Python/TypeScript/Go SDKs; MCP server available
- **Pricing:** Cloud (enterprise) OR self-hosted (Graphiti is OSS)
- **Fleet Relevance:** ✅ Excellent for complex multi-agent scenarios. Graph structure enables relationship queries. Paper published (arXiv:2501.13956)

#### **Memori** (MemoriLabs/Memori)
- **Stars:** 14,548 | **Language:** Python/TypeScript
- **Architecture:** Agent-native memory infrastructure; LLM-agnostic layer
- **Storage:** Cloud (managed) OR BYODB (bring your own database)
- **Retrieval:** Claims 81.95% on LoCoMo with 1,294 tokens/query (~5% of full-context)
- **Key Innovation:** Automatic attribution (entity_id/process_id); automatic memory capture/recall without agent code changes
- **Integration:** OpenClaw plugin, Hermes Agent provider, MCP support
- **Pricing:** Cloud API or BYODB (self-hosted)
- **Fleet Relevance:** ⚠️ Has OpenClaw plugin specifically. BYODB option is good for fleet.

#### **mcp-memory-service** (doobidoo/mcp-memory-service)
- **Stars:** 1,850 | **Language:** Python
- **Architecture:** Self-hosted memory service with REST API + MCP
- **Storage:** SQLite (default) + optional cloud sync (S3/R2/D1)
- **Retrieval:** Hybrid semantic + BM25 + ONNX local embeddings
- **Key Innovation:** Knowledge graph with typed edges (causes, fixes, contradicts); autonomous consolidation; OAuth 2.0 + Remote MCP for claude.ai browser
- **Integration:** 76 REST endpoints, MCP, works with LangGraph/CrewAI/AutoGen/Claude Code/OpenClaw
- **Pricing:** Fully open source, zero per-call cost
- **Fleet Relevance:** ✅ Strong. Local embeddings (privacy), multi-agent tagging via X-Agent-ID header, inter-agent messaging via tags

#### **PLUR** (plur-ai/plur)
- **Stars:** 123 (core) | **Language:** TypeScript
- **Architecture:** Local-first, file-based (YAML) persistent memory
- **Storage:** Plain YAML files on disk (~/.plur/)
- **Retrieval:** BM25 + BGE embeddings + Reciprocal Rank Fusion (fully local, zero API calls)
- **Key Innovation:** ACT-R activation decay model - memories fade naturally; cross-tool sharing (Claude Code, Cursor, Windsurf, OpenClaw, Hermes)
- **Integration:** MCP server, OpenClaw ContextEngine plugin, Hermes plugin
- **Pricing:** Free, local-only
- **Fleet Relevance:** ✅ Specifically mentions OpenClaw support. Good for local-first, privacy-sensitive deployments.

### Tier 2: Emerging / Specialized

#### **Memora** (agentic-box/memora)
- **Stars:** 405 | **Language:** Python
- **Architecture:** MCP-native memory with SQLite + optional cloud sync
- **Storage:** SQLite local, S3/R2/D1 cloud sync
- **Retrieval:** Semantic (TF-IDF, sentence-transformers, or OpenAI)
- **Key Innovation:** Hierarchical organization (section/subsection), document fragment storage, LLM-powered deduplication
- **Integration:** MCP server, works with Claude Code/Codex
- **Fleet Relevance:** ✅ Good feature set, newer project (less mature)

#### **AgentMemory** (rohitg00/agentmemory)
- **Stars:** 10,802 | **Language:** TypeScript
- **Architecture:** "#1 Persistent memory for AI coding agents based on real-world benchmarks"
- **Limited technical details in README** - appears focused on coding agents specifically

#### **MemOS** (MemTensor/MemOS)
- **Stars:** 9,141 | **Language:** TypeScript
- **Architecture:** "Self-evolving memory OS" with hybrid-retrieval and cross-task skill reuse
- **Claims 35.24% token savings**

### Tier 3: Mentioned but Limited Data

- **MCP Agora** (thebnbrkr/agora-code) - 30 stars, codebase intelligence for AI coding agents
- **Pluribus** (johnnyjoy/pluribus) - 9 stars, Go-based MCP memory server
- **MemPalace** - viral April 2026, but benchmark methodology questioned by community

---

## 2. Technical Approaches Comparison

| Approach | Examples | Best For | Trade-offs |
|----------|----------|----------|------------|
| **Vector Stores** | Mem0, Memora, mcp-memory-service | Semantic similarity search, simple facts | Can miss exact matches, no relationship context |
| **Structured Storage (Graph)** | Zep/Graphiti, mcp-memory-service (edges) | Complex relationships, reasoning about connections | Higher complexity, needs graph DB |
| **Temporal Graphs** | Zep/Graphiti, Mem0 (new algorithm) | State changes over time, "what was true then" | Most complex, requires temporal reasoning |
| **File-Based** | PLUR | Simplicity, local-first, version control | Limited scale, no concurrent access |
| **Protocol-Level (MCP)** | All MCP-native solutions | Tool-agnostic integration | Dependent on MCP adoption |

### Retrieval Method Breakdown

All major solutions have converged on **hybrid retrieval**:

1. **Semantic Search** - Vector embeddings for conceptual similarity
2. **Keyword Search (BM25)** - Exact term matching with TF-IDF weighting
3. **Entity Matching** - Boost results containing known entities
4. **Graph Traversal** - Follow relationships (Zep/Graphiti)
5. **Temporal Scoring** - Prefer recent or time-relevant memories (Mem0, Zep)

**Fusion Method:** Reciprocal Rank Fusion (RRF) is the consensus approach - combines multiple signals without requiring score calibration.

---

## 3. Storage Mechanisms Comparison

| Backend | Used By | Pros | Cons |
|---------|---------|------|------|
| **Qdrant** | Mem0 (default) | Fast, built-in hybrid search, metadata filtering | Additional service to run |
| **Chroma** | Mem0 | Simple, in-process option | Less performant at scale |
| **PGVector** | Mem0, general | Use existing Postgres | Not specialized for vectors |
| **Neo4j** | Zep/Graphiti | Native graph operations | Complex, resource-intensive |
| **SQLite** | mcp-memory-service, Memora | Zero-config, portable, single file | Limited concurrency |
| **FalkorDB** | Zep/Graphiti | Fast graph in Redis | Less mature than Neo4j |
| **Kuzu** | Zep/Graphiti | Embedded graph DB, DuckDB-like | Newer, smaller ecosystem |
| **S3/R2/D1** | mcp-memory-service, Memora | Cloud sync, durability | Latency, eventual consistency |
| **Redis** | Mem0, langgraph-redis | Fast, good for caching | Memory-only by default |
| **Local Files (YAML)** | PLUR | Version control, inspectable | No query capabilities |

---

## 4. Integration Patterns

### Pattern 1: Direct SDK/Library
- **Mem0:** `pip install mem0ai` or `npm install mem0ai`
- **Zep:** `pip install zep-cloud` or `npm install @getzep/zep-cloud`
- **Memori:** `pip install memori` or `npm install @memorilabs/memori`

**Pros:** Tight integration, type safety, framework helpers
**Cons:** Vendor lock-in, language-specific

### Pattern 2: MCP (Model Context Protocol)
- **PLUR:** `npx @plur-ai/mcp init`
- **mcp-memory-service:** Configure in `.mcp.json`
- **Memora:** `memora-server` in MCP config

**Pros:** Tool-agnostic, Claude Code/Cursor/Windsurf/OpenClaw all support MCP
**Cons:** MCP is still evolving, transport variations (stdio vs HTTP)

### Pattern 3: REST API
- **Mem0:** Cloud API with API keys
- **mcp-memory-service:** 76 REST endpoints
- **Zep:** Cloud API

**Pros:** Universal, any HTTP client
**Cons:** Network latency, authentication complexity

### Pattern 4: Plugin/Extension
- **Memori:** OpenClaw plugin, Hermes provider
- **PLUR:** OpenClaw ContextEngine plugin

**Pros:** Native integration, automatic lifecycle hooks
**Cons:** Platform-specific implementation needed

### Pattern 5: LLM Middleware (Transparent)
- **Memori:** `mem.llm.register(client)` - wraps OpenAI client, auto-captures

**Pros:** Zero code changes to existing agents
**Cons:** Magic/unpredictable when it fires

---

## 5. Limitations and Failure Modes

### Retrieval Failures

| Failure Mode | Cause | Mitigation |
|--------------|-------|------------|
| **Missed relevant memories** | Embedding drift, poor query formulation | Hybrid search (BM25 backup), query expansion |
| **Too many irrelevant hits** | Broad semantic similarity, noisy embeddings | Reranking, threshold tuning, metadata filtering |
| **Stale memories returned** | No decay mechanism | Temporal scoring, activation decay (PLUR), consolidation |
| **Missing relationships** | Vector-only storage | Graph structure (Zep), entity linking (Mem0) |

### Storage/Scale Failures

| Failure Mode | Cause | Mitigation |
|--------------|-------|------------|
| **Vector DB overload** | Too many embeddings, high dimensionality | HNSW indexing, dimension reduction, sharding |
| **SQLite locking** | Concurrent writes | Write-ahead logging, queue-based writes, Postgres |
| **Memory bloat** | Unbounded accumulation | TTL, decay, consolidation, manual cleanup |
| **Sync conflicts** | Multi-device cloud sync | CRDTs, last-write-wins with timestamps, git-based (PLUR) |

### Integration Failures

| Failure Mode | Cause | Mitigation |
|--------------|-------|------------|
| **Context pollution** | Too many memories injected | Token budget management, relevance scoring, limit enforcement |
| **Agent hallucination from memory** | Outdated/wrong memories | Confidence scoring, source attribution, human feedback loop |
| **Privacy leakage** | Shared memory without isolation | Entity scoping, filter enforcement, separate DBs per tenant |

---

## 6. Fleet Relevance Assessment for OpenClaw

### Current OpenClaw State
- Uses lossless-claw for conversation history (compacted summaries)
- Has MEMORY.md for long-term curated memory
- Has daily notes (memory/YYYY-MM-DD.md) for raw logs
- GX-10 (192.168.50.30) hosts local inference + shared knowledge base at :8100

### Recommended Approaches

#### **Option A: Augment Existing System (Recommended)**
Keep current file-based memory but add:
1. **Semantic search over MEMORY.md + daily notes** - Use GX-10's embeddings endpoint (:8082) to build local search
2. **Hybrid retrieval** - BM25 (ripgrep) + embeddings for robustness
3. **Entity extraction** - Tag entries with projects, people, decisions

**Pros:** Maintains human-readable files, no new dependencies, leverages existing GX-10 infrastructure
**Cons:** Manual curation still needed, no automatic decay/consolidation

#### **Option B: Add PLUR (Lightweight)**
Install PLUR for automatic cross-session learning:
```bash
openclaw plugins install @plur-ai/claw
openclaw config set plur.enabled true
```

**Pros:** Zero config, designed for OpenClaw, local-only, version-controllable
**Cons:** YAML-based (limited scale), newer project (v0.9.4)

#### **Option C: Add Memori (Full-Featured)**
```bash
openclaw plugins install @memorilabs/openclaw-memori
```

**Pros:** Purpose-built OpenClaw plugin, automatic capture, BYODB option
**Cons:** External dependency, cloud service or self-hosted complexity

#### **Option D: Self-Hosted mcp-memory-service**
Run on GX-10 as shared memory for all agents:
```bash
pip install mcp-memory-service
memory server --http  # On GX-10
```

**Pros:** Full control, knowledge graph, multi-agent tagging, local embeddings
**Cons:** Additional service to maintain, SQLite concurrency limits

#### **Option E: Mem0 Self-Hosted**
```bash
cd server && make bootstrap  # Docker compose
```

**Pros:** Most mature, comprehensive, proven at scale
**Cons:** Requires Qdrant/Postgres stack, heavier resource footprint

### Decision Matrix

| Criteria | File-Based + Enhance | PLUR | Memori | mcp-memory-service | Mem0 |
|----------|---------------------|------|--------|-------------------|------|
| **Simplicity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Multi-Agent** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Automatic Learning** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Privacy/Local** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Relationship Tracking** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Maturity** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Fleet Integration** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 7. Key Technical Insights

### What's Working Well
1. **Hybrid retrieval is consensus** - Every mature solution uses semantic + keyword + fusion
2. **Local embeddings are viable** - sentence-transformers, ONNX runtime eliminate cloud dependency
3. **MCP is becoming standard** - Tool-agnostic integration reduces per-platform work
4. **Entity scoping is essential** - Multi-agent requires user_id/agent_id/run_id filtering

### Open Problems
1. **Consolidation/summarization** - Automatic compression of old memories is hard; most solutions punt to manual cleanup
2. **Cross-agent coordination** - Shared memory is solved (tags), but conflict resolution is not
3. **Evaluation** - No standard benchmark; LongMemEval and LoCoMo gaining traction but imperfect
4. **Cost/latency trade-offs** - Local = cheap but slower; cloud = fast but expensive at scale

### Emerging Patterns
1. **Temporal awareness** - Zep/Graphiti and Mem0 v3 both emphasize validity windows
2. **Agent-generated facts** - Treating agent outputs as first-class memories, not just user input
3. **Activation decay** - PLUR's ACT-R model may spread; auto-pruning stale memories is valuable
4. **Knowledge graphs over vectors** - For complex reasoning, relationships matter more than similarity

---

## 8. Actionable Recommendations

### Immediate (This Week)
1. **Evaluate PLUR** - Install and test with a single project; minimal risk
2. **Search enhancement** - Add semantic search to existing MEMORY.md using GX-10 embeddings

### Short-Term (This Month)
1. **Prototype mcp-memory-service** on GX-10 for multi-agent shared memory
2. **Define entity model** - Standardize user_id/agent_id/run_id conventions across fleet

### Medium-Term (This Quarter)
1. **Benchmark** - Test PLUR vs mcp-memory-service vs enhanced file-based on real OpenClaw tasks
2. **Decision** - Pick one primary approach and deprecate others
3. **Document** - Write fleet memory conventions guide

---

## References

- Mem0: https://github.com/mem0ai/mem0 | docs.mem0.ai
- Zep/Graphiti: https://github.com/getzep/graphiti | https://www.getzep.com
- Memori: https://github.com/MemoriLabs/Memori | memorilabs.ai
- mcp-memory-service: https://github.com/doobidoo/mcp-memory-service
- PLUR: https://github.com/plur-ai/plur | plur.ai
- Memora: https://github.com/agentic-box/memora
- LoCoMo benchmark: Long-Context Multi-Session Evaluation
- LongMemEval: Long Context Memory Evaluation

---

*Report generated by subagent for OpenClaw fleet architecture review.*

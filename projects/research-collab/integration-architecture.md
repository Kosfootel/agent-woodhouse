# Agent Fleet Integration Architecture
**Document:** Agent Knowledge Persistence + Context Transfer + Task Patterns  
**Version:** 1.1 — Mesh Memory Only (A2A Deprecated)  
**Date:** 2026-06-10  
**Status:** Awaiting Liz Mesh Memory Completion  
**Author:** Woodhouse

---

## Executive Summary

This document specifies how three agent systems integrate into a unified knowledge and coordination layer using **Mesh Memory only** (A2A deprecated per 2026-06-10 update from Mr. Ross).

1. **Skill Journal** — Persistent organizational memory (Mesh Memory backed)
2. **Context Capsules** — Reversible conversation state for handoffs (transient + optional archive)
3. **Task Patterns** — Proven multi-agent coordination strategies (reference + state machine)

**Core Principle:** With Mesh Memory as the single source of truth, agents read shared state directly rather than coordinating via point-to-point A2A. This eliminates protocol complexity and ensures consistency.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT FLEET                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ Woodhouse│  │   Ray    │  │   Liz    │  ← Individual agents │
│  │ (.24)    │  │ (.22)    │  │ (.23)    │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
│       │             │             │                              │
│       └─────────────┴─────────────┘                              │
│                     │                                            │
│              ┌──────▼──────┐                                     │
│              │  MESH MEMORY│  ← Unified shared state             │
│              │  (GX-10)    │    (all coordination via reads)     │
│              └─────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘

Key Change: No A2A protocol layer. Agents coordinate by reading/writing 
to Mesh Memory directly.
```

---

## Layer 1: Context Capsules (Foundation)

### Purpose
Enable rich, reversible handoffs between agents without information loss from text summarization.

### Specification: CC-1 Format

**Schema:**
```yaml
context_capsule:
  _cc:
    v: "1.0"                    # Version for compatibility
    ts: "2026-06-10T10:00:00Z"  # Creation timestamp
    tok: 847                    # Token count
    src: "agent:main:..."       # Source session
  
  intent:
    primary: "debug_connection"
    secondary: ["verify_config"]
    confidence: 0.87
    evolved_from: "initial_complaint"
  
  user:
    pref:
      detail_level: "technical"
      verbosity: "concise"
    state:
      frustration: 0.3
      urgency: 0.8
    mentioned:
      tools: ["curl", "wireshark"]
      constraints: ["cannot_restart_prod"]
  
  conversation:
    stage: "investigation"
    pending_questions: ["what_changed_recently"]
    blockers: ["missing_log_access"]
  
  actions:
    completed: [...]
    attempted_failed: [...]
    planned: [...]
  
  knowledge:
    confirmed: {timeout_occurs: true}
    inferred: {likely_cdn_issue: 0.7}
    unknown: ["recent_deployment_history"]
  
  semantic:
    embedding_b64: "..."        # Optional
    dim: 768
    model: "text-embedding-3-small"
  
  verbatim:
    critical_quotes:
      - speaker: "user"
        text: "Started exactly 2 days ago after maintenance"
        importance: 0.95
    exact_values:
      timeout_seconds: "30"
      error_code: "524"
  
  narrative: "High-level summary for quick scan"
```

### Token Budgets by Use Case

| Tier | Tokens | Use Case |
|------|--------|----------|
| Minimal | 300-500 | Simple handoffs, token-constrained |
| Standard | 600-1100 | Most subagent spawns |
| Full | 1000-1800 | Complex research/analysis tasks |

### Persistence Model

**Transient:** Capsules primarily exist during handoff
**Optional Archive:** May persist to Mesh Memory for:
- Debugging handoff failures
- Training data for capsule quality
- Audit trails for multi-step workflows

---

## Layer 2: Task Patterns (Coordination)

### Purpose
Proven strategies for organizing multi-agent work with documented failure modes and recovery.

### Pattern Catalog Summary

| Pattern | Core Mechanism | Key Primitive |
|---------|---------------|---------------|
| Fan-Out | Parallel independent subagents | `sessions_spawn` + `sessions_yield` |
| Pipeline | Sequential stages with gates | Capsule handoff between stages |
| Voting | Multiple agents, result aggregation | Variant prompts, consensus logic |
| Monitor/Delegate | Parent oversight with checkpointing | Capsule state + intervention |
| TaskFlow | Durable multi-step with persistence | `stateJson` with embedded capsule |
| Agency Agent | Specialized persona delegation | `~/.openclaw/agency-agents/` |

### Integration with Context Capsules

**Critical dependency:** All patterns benefit from capsules

| Pattern | Capsule Role |
|---------|--------------|
| Fan-Out | Each subagent gets capsule subset relevant to its task |
| Pipeline | Capsule is primary handoff mechanism between stages |
| Voting | Base capsule distributed to all voters for consistency |
| Monitor/Delegate | Checkpoint capsule enables progress assessment |
| TaskFlow | `stateJson` embeds capsule for durable state |
| Agency Agent | Capsule carries user context into specialized domain |

### Failure Mode → Skill Journal Logging

Each pattern has documented failure modes that should auto-log:

```yaml
skill_entry_trigger:
  pattern: "TaskFlow"
  failure_mode: "revision_conflict"
  action: "auto_log_skill"
  data:
    problem: "Concurrent TaskFlow mutation"
    solution: "Retry with latest revision"
    success_rate: 0.95  # Measured from retries
```

---

## Layer 3: Skill Journal (Organizational Memory)

### Purpose
Agents learn from each other across sessions — curated, queryable, mesh-replicated.

### Storage Architecture (4-Layer)

```
Layer 1: Entries
├── memory/skill-journal/entries/YYYY/MM/*.yaml
└── Individual skill artifacts (YAML)

Layer 2: Index
├── memory/skill-journal/index.yaml
└── Fast pattern/tag/domain lookup

Layer 3: Embeddings
├── GX-10 vector store
└── Semantic search capability

Layer 4: Mesh Sync
├── A2A protocol extension
└── Cross-agent skill sharing
```

### Schema

```yaml
skill_entry:
  id: "skill-{timestamp}-{hash}"
  version: "1.0"
  
  source:
    agent: "Woodhouse"
    session: "agent:main:..."
    timestamp: "2026-06-10T10:00:00-04:00"
    parent_task: "task-id"
  
  problem:
    pattern: "mcp-timeout-handling"
    description: "MCP tools hanging when upstream down"
    domain: ["mcp", "async"]
    severity: "high"
    frequency: "recurring"
  
  solution:
    approach: "Circuit breaker with timeout"
    steps: ["Wrap in asyncio.wait_for()", "Exponential backoff"]
    rationale: "Prevents cascading failures"
  
  implementation:
    tools_used:
      - tool: "asyncio"
        purpose: "timeout"
    code_snippet: "..."
    file_refs:
      - path: "src/mcp/client.py"
        commit: "abc123"
  
  lessons: ["Default MCP has no timeout"]
  gotchas: ["asyncio.wait_for cancels but no cleanup guarantee"]
  
  tags: ["mcp", "asyncio", "timeout", "resilience"]
  
  related:
    - skill_id: "skill-2026-05-20-abc"
      relationship: "extends"
  
  status: "active"  # active | deprecated | superseded
  access_count: 0
  last_accessed: null
```

### Query Interface

**Natural Language:**
```python
result = skill_journal.query("Has anyone solved MCP timeout issues?")
```

**Structured:**
```python
result = skill_journal.find_by_pattern("mcp-timeout-handling")
result = skill_journal.find_by_domain(domain="mcp", subdomain="timeout")
result = skill_journal.find_by_tools(tools=["asyncio", "tenacity"])
```

### Integration Points

| System | Integration |
|--------|-------------|
| Context Capsules | Capsule's `semantic.embedding` enables similarity search against journal |
| Task Patterns | Pattern selection queries journal: "which pattern worked for similar tasks?" |
| Mesh Memory | Skills replicate across agents via Mesh Sync layer |

---

## Cross-Layer Integration: The Full Flow

### Scenario: Complex Task Execution

```
User Request: "Debug why Vigil dashboard isn't loading"

┌────────────────────────────────────────────────────────────────┐
│ STAGE 1: INTAKE                                                │
│ Woodhouse (main)                                               │
│                                                                │
│ 1. Query Skill Journal:                                        │
│    "vigil dashboard loading issues"                            │
│    → Found: skill-2026-05-15-vigil-nginx-timeout               │
│                                                                │
│ 2. Build Context Capsule (CC-1 Standard):                      │
│    - Intent: debug_vigil_dashboard                             │
│    - User state: urgency 0.9, knowledge level: expert          │
│    - Known from skill: check nginx timeout first               │
│                                                                │
│ 3. Select Pattern: TaskFlow (multi-step, durable)             │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ STAGE 2: TASKFLOW ORCHESTRATION                                │
│                                                                │
│ TaskFlow.createManaged():                                      │
│   stateJson: {                                                 │
│     capsule: {...CC-1...},                                     │
│     stage: "diagnosis",                                        │
│     skills_consulted: ["skill-2026-05-15-vigil-nginx-timeout"] │
│   }                                                            │
│                                                                │
│ TaskFlow.runTask():                                            │
│   Spawn security-engineer (agency agent)                       │
│   Pass capsule in context                                      │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ STAGE 3: FAN-OUT INVESTIGATION                                 │
│ Security-agent receives capsule                                │
│                                                                │
│ 1. Query Skill Journal for security patterns:                  │
│    "nginx timeout security implications"                       │
│                                                                │
│ 2. Spawn 3 subagents in parallel:                              │
│    - Check nginx config                                        │
│    - Check Tailscale connectivity                              │
│    - Check GX-10 resource usage                                │
│                                                                │
│ 3. Each subagent gets capsule subset relevant to task         │
│    - Subagent 1: nginx-focused capsule                         │
│    - Subagent 2: network-focused capsule                       │
│    - Subagent 3: resource-focused capsule                      │
│                                                                │
│ 4. sessions_yield for all 3                                    │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ STAGE 4: PIPELINE SYNTHESIS                                    │
│                                                                │
│ Results merged → Updated capsule:                              │
│   - Root cause: GX-10 OOM during peak load                     │
│   - Actions taken: [list]                                    │
│   - Knowledge confirmed: [facts]                             │
│                                                                │
│ TaskFlow.runTask():                                            │
│   Spawn backend-architect for fix                              │
│   Pass updated capsule                                         │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ STAGE 5: SKILL CAPTURE                                         │
│                                                                │
│ Fix implemented → TaskFlow.finish():                           │
│                                                                │
│ 1. Extract new skill:                                          │
│    - Problem: "Vigil OOM during peak load"                     │
│    - Solution: "Increase GX-10 swap, add memory alerts"        │
│    - Pattern: "resource-exhaustion-detection"                │
│                                                                │
│ 2. Write to Skill Journal:                                     │
│    - Local entry created                                       │
│    - Mesh Sync queues for replication                          │
│                                                                │
│ 3. Archive final capsule to Mesh Memory (optional)             │
└────────────────────────────────────────────────────────────────┘
```

---

## Mesh Topology: Mesh Memory Only

**Updated 2026-06-10:** Per Mr. Ross, A2A is deprecated. All coordination flows through Mesh Memory.

### Previous Model (A2A + Mesh Memory)
- A2A for live handoffs, queries, coordination signals
- Mesh Memory for persistence
- **Complexity:** Two protocols, potential inconsistency

### New Model (Mesh Memory Only)
- Mesh Memory serves both live coordination AND persistence
- **Simplification:** Single source of truth
- **Trade-off:** Slightly higher read latency acceptable for consistency

### Data Type Mapping (Updated)

| Data | Storage | Access Pattern | Lifetime |
|------|---------|----------------|----------|
| Context Capsules | Transient (handoff) + optional Mesh archive | Write at handoff, read by child | Session or persistent |
| Skill Entries | Mesh Memory | Read on query, write on capture | Permanent |
| Skill Index | Mesh Memory | Query via search interface | Permanent |
| Embeddings | Mesh Memory (vector store) | Semantic similarity search | Permanent |
| Pattern Library | Mesh Memory + local cache | Read on pattern selection | Permanent, cache locally |
| TaskFlow State | TaskFlow API + Mesh persistence | Read/write during orchestration | Until completion |

### Coordination via Mesh Memory

**Previous (A2A):**
```
Woodhouse: "Hey Liz, got any skills on MCP timeouts?"
Liz: "Yeah, here's skill-xyz..."
```

**New (Mesh Memory):**
```
Woodhouse: query_mesh_memory(
  type: "skill",
  pattern: "mcp-timeout",
  domain: ["mcp", "async"]
)
→ Returns: [skill-xyz, skill-abc]  // Direct read, no protocol
```

**Benefits:**
- No protocol implementation overhead
- Natural caching (read same skill multiple times)
- Conflict resolution at storage layer (Mesh Memory handles revisions)
- Easier debugging (all state visible in one place)

---

## Implementation Phases

### Phase 1: Local Foundation (Woodhouse Only)

**Goal:** Validate individual systems before mesh integration

| System | Deliverable | Success Criteria |
|--------|-------------|------------------|
| Context Capsules | `tools/capsule_builder.py` | Build/rehydrate CC-1, <1100 tokens, no info loss |
| Skill Journal | `memory/skill-journal/` structure | 10+ entries, query works, <2s retrieval |
| Task Patterns | Documented + used | 3 patterns used in production |

**No mesh dependencies in Phase 1.**

### Phase 2: Liz Mesh Memory Integration

**Prerequisite:** Liz's mesh memory architecture finalized

**Goal:** Skills persist across agents

| Deliverable | Depends On |
|-------------|------------|
| Skill Journal sync protocol | Liz's Mesh Memory write API |
| Embeddings on GX-10 | Liz's vector store interface |
| Cross-agent skill queries | Liz's mesh query protocol |
| Conflict resolution (same skill, different agents) | Liz's revision model |

**Open Questions for Liz:**
1. What's the Mesh Memory write API? (file-based, REST, other?)
2. How are conflicts resolved? (last-write-wins, merge, manual?)
3. What's the latency for cross-agent reads?
4. Is there a pub/sub mechanism for "new skill available"?
5. How are embeddings stored and queried?

### Phase 3: Ray + Full Mesh

**Goal:** All three agents (Woodhouse, Ray, Liz) share knowledge

- Skill Journal replicates to all agents
- Pattern library is fleet-wide
- TaskFlow can orchestrate across agents
- Capsules can handoff between any agent pair

### Phase 4: Auto-Capture & Intelligence

**Goal:** Systems operate with minimal explicit action

- Auto-detect novel problems → suggest skill capture
- Pattern selection based on skill journal success rates
- Capsule compression auto-optimizes based on task type
- Predictive skill queries ("you might need this...")

---

## Dependencies on Liz (Updated)

### Blocking for Phase 2

| Need | From Liz | Impact if Unavailable |
|------|----------|----------------------|
| Mesh Memory read API | Query interface | Cannot read shared skills/patterns |
| Mesh Memory write API | Storage interface | Skills stay local only |
| Embeddings query | Vector search | Semantic search limited |
| Conflict resolution | Revision model | Concurrent edits may lose data |
| Change notification | Pub/sub or polling | Agents don't know when new skills available |

### Non-Blocking (Can Proceed)

- Context Capsule format (purely local, no storage needed)
- Task Pattern documentation (reference material)
- Skill Journal local structure (YAML files)

### Preferred Collaboration Model

1. **Async documentation review:** Liz reviews this spec, comments on Mesh Memory integration
2. **Interface definition:** Liz provides Mesh Memory API contract (read/write/query)
3. **Joint test:** Single skill write/read via Mesh Memory
4. **Rollout:** Full fleet replication

**Note:** With A2A deprecated, the "mesh sync protocol" question becomes "Mesh Memory replication protocol" — how do writes on Woodhouse propagate to Liz's view of Mesh Memory?

---

## Success Metrics

### Phase 1 (Local)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Capsule retrieval time | <2s | Build + rehydrate latency |
| Capsule token efficiency | <50% of original | (tokens in capsule) / (original conv tokens) |
| Skill query precision | >80% | Relevant skills in top-3 results |
| Pattern adoption | >50% of multi-agent tasks | Tasks using documented patterns |

### Phase 2+ (Mesh)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cross-agent skill retrieval | <5s | Query time including mesh latency |
| Skill reuse rate | >40% | Skills accessed by agent other than creator |
| Mesh sync reliability | >99% | Skills successfully replicate |
| Conflict resolution | <1% manual | Auto-resolved vs escalated |

---

## Open Questions

### Technical

1. **Embedding model selection:** text-embedding-3-small vs local alternatives?
2. **Capsule compression:** Worth binary encoding (MessagePack, CBOR) for size?
3. **Skill expiration:** Should skills auto-deprecate after N months without access?
4. **Privacy:** Some skills may be agent-private (not mesh-shared) — how to mark?

### Coordination

1. **Skill ownership:** Who can edit/delete a skill? (original creator, any agent, human only?)
2. **Validation:** Should skills require human approval before mesh publication?
3. **Pattern governance:** Who updates the pattern library? (living document)
4. **Conflict escalation:** When do agents ask humans vs auto-resolve?

### Fleet

1. **Ray's role:** Does Ray need Skill Journal? (Commerce focus may have different needs)
2. **Agency agent integration:** Do agency agents get their own skill journals?
3. **Human skill input:** Can humans write skills directly? (e.g., "always check X first")

---

## Appendix A: File Structure

```
memory/
├── skill-journal/
│   ├── index.yaml
│   ├── entries/
│   │   └── 2026/
│   │       └── 06/
│   │           └── skill-2026-06-10-*.yaml
│   ├── patterns/
│   │   └── extracted-reusable-patterns.yaml
│   └── mesh-sync.yaml
│
├── knowledge/
│   └── projects/
│       ├── skill-journal-research.md
│       ├── context-capsule-research.md
│       ├── task-patterns-library.md
│       └── integration-architecture.md (this file)
│
├── fleet_kb.md
├── commitments/
└── capsule-archive/  # Optional
    └── 2026/
        └── 06/
            └── capsule-*.json

tools/
├── skill_journal.py          # CLI for CRUD + query
├── capsule_builder.py        # Build/rehydrate CC-1
└── pattern_selector.py       # Query patterns, get recommendations
```

---

## Appendix B: Mesh Memory API (Proposed — Awaiting Liz)

### Operations

```yaml
# Read skill by ID
mesh_memory.read:
  type: "skill"
  id: "skill-2026-06-10-abc"

# Query skills
mesh_memory.query:
  type: "skill"
  filter:
    pattern: "mcp-*"
    domain: ["mcp", "async"]
    status: "active"
  sort: "recency"
  limit: 5

# Semantic search
mesh_memory.semantic_search:
  type: "skill"
  embedding: [0.1, 0.2, ...]  # Vector
  similarity_threshold: 0.8

# Write skill
mesh_memory.write:
  type: "skill"
  id: "skill-2026-06-10-abc"
  content: {...yaml content...}
  options:
    conflict_resolution: "merge" | "overwrite" | "fail"

# Subscribe to changes (optional pub/sub)
mesh_memory.subscribe:
  type: "skill"
  pattern: "*"
  callback: "notify_new_skill"

# Pattern library read
mesh_memory.read:
  type: "pattern_library"
  name: "pipeline"
```

### Notes

- **Consistency model:** Eventual consistency acceptable for skills
- **Latency target:** < 500ms for read, < 1s for write acknowledgment
- **Caching:** Agents may cache pattern library locally; skills query fresh
- **Versioning:** Implicit via revision IDs in Mesh Memory

---

## Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-06-10 | 1.0 | Initial integration architecture spec |

---

*Document Status: Planning phase — awaiting Liz Mesh Memory coordination*
*Next Update: After Liz interface definition*

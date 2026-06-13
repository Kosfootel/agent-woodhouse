# Skill Journal — Research & Design Document

**Date:** 2026-06-10  
**Researcher:** Woodhouse (Subagent)  
**Status:** Design Phase

---

## 1. Research Summary: Existing Approaches

### 1.1 Knowledge Graphs (Academic/Enterprise)
- **Concept:** Nodes (entities/concepts) connected by edges (relationships)
- **Pros:** Rich semantic relationships, inference capabilities
- **Cons:** Complex to maintain, requires structured ontology, query overhead
- **Examples:** RDF triplestores, Neo4j, enterprise knowledge management
- **Verdict:** Overkill for agent skill persistence; too much overhead for lightweight use

### 1.2 Experience Databases / Case-Based Reasoning (CBR)
- **Concept:** Store past problem→solution pairs, retrieve by similarity
- **Pros:** Proven in helpdesk/troubleshooting systems
- **Cons:** Similarity matching is hard; needs good indexing
- **Examples:** Academic CBR systems, some support ticket platforms
- **Verdict:** Good conceptual fit, but needs modern vector embedding for similarity

### 1.3 Pattern Libraries / Playbooks (DevOps/Security)
- **Concept:** Curated reusable patterns for common scenarios
- **Pros:** Human-readable, versioned, collaborative
- **Cons:** Manual curation, can become stale
- **Examples:** Kubernetes patterns, security playbooks, design patterns
- **Verdict:** Right abstraction level, but needs automated capture

### 1.4 Fleet-KB + Commitments (Current Fleet Approach)
- **Fleet-KB:** Semantic knowledge base for projects (markdown, human-readable)
- **Commitments:** Structured YAML for decisions/facts with source attribution
- **Pattern:** Tier 1 = exact recall (commitments), Tier 2 = semantic search (fleet-kb)
- **Verdict:** Excellent foundation; Skill Journal extends this model

---

## 2. Skill Journal: Core Concept

**A Skill Journal entry is a curated learning artifact capturing:**
- What problem was solved (pattern)
- How it was solved (approach + tools)
- What went wrong (gotchas, failures)
- Where to find more (artifacts, references)
- Who solved it (provenance for follow-up)

**Key Difference from Commitments:**
- Commitments = "what we decided" (facts, decisions)
- Skill Journal = "how we solved it" (procedures, lessons)

---

## 3. Data Model

### 3.1 Core Schema (YAML)

```yaml
skill_entry:
  # Identity
  id: "skill-{timestamp}-{hash}"
  version: "1.0"
  
  # Provenance
  source:
    agent: "Woodhouse"                    # Who solved it
    session: "agent:main:telegram:..."    # Session context
    timestamp: "2026-06-10T09:50:00-04:00"
    parent_task: "task-id-if-delegated"   # Link to parent
  
  # Problem Classification
  problem:
    pattern: "mcp-tool-timeout-handling"   # Machine-readable tag
    description: "MCP tools hanging indefinitely when upstream service is down"
    domain: ["mcp", "async", "error-handling"]  # Taxonomy
    severity: "high"                       # impact level
    frequency: "recurring"                 # one-off | recurring | systematic
  
  # Solution Approach
  solution:
    approach: "Implement circuit breaker with timeout wrapper"
    steps:
      - "Wrap MCP calls in asyncio.wait_for()"
      - "Set default timeout to 30s"
      - "Implement exponential backoff retry"
      - "Log timeout events for monitoring"
    rationale: "Prevents cascading failures when MCP server degrades"
  
  # Implementation Details
  implementation:
    tools_used:
      - tool: "asyncio"
        purpose: "timeout handling"
      - tool: "tenacity"
        purpose: "retry logic"
    code_snippet: |
      @retry(stop=stop_after_attempt(3), wait=wait_exponential())
      async def call_with_timeout(func, timeout=30):
          try:
              return await asyncio.wait_for(func(), timeout=timeout)
          except TimeoutError:
              logger.error("MCP call timed out")
              raise CircuitBreakerOpen()
    file_refs:
      - path: "src/mcp/client.py"
        commit: "abc123"
  
  # Learnings & Gotchas
  lessons:
    - "Default MCP client has no timeout — always wrap"
    - "Tenacity retry count should be configurable"
    - "Circuit breaker state should be observable in logs"
  
  gotchas:
    - "asyncio.wait_for() cancels the task but doesn't guarantee cleanup"
    - "Some MCP servers don't handle cancellation gracefully"
  
  # Validation
  validation:
    tested: true
    test_refs:
      - "tests/test_mcp_timeout.py"
    verified_by: "Woodhouse"
    verified_at: "2026-06-10T10:15:00-04:00"
  
  # Discovery
  tags:
    - "mcp"
    - "asyncio"
    - "timeout"
    - "circuit-breaker"
    - "resilience"
  
  related:
    - skill_id: "skill-2026-05-20-abc"     # Link to similar skill
      relationship: "extends"
    - skill_id: "skill-2026-06-01-def"
      relationship: "alternative-approach"
  
  # Lifecycle
  status: "active"                         # active | deprecated | superseded
  superseded_by: null                      # skill_id if deprecated
  access_count: 0                          # Times retrieved
  last_accessed: null
```

### 3.2 Simplified Entry (Quick Capture)

For rapid capture during problem-solving:

```yaml
skill_quick:
  id: "skill-quick-{timestamp}"
  source:
    agent: "Woodhouse"
    session: "..."
    timestamp: "2026-06-10T09:50:00-04:00"
  problem: "Brief description of what went wrong"
  solution: "What fixed it"
  tools: ["tool1", "tool2"]
  gotcha: "The one thing that bit me"
  tags: ["domain", "tech"]
  status: "draft"                          # Can be promoted to full entry
```

---

## 4. Storage Architecture

### 4.1 Directory Structure

```
memory/
├── skill-journal/                    # NEW: Skill Journal entries
│   ├── index.yaml                    # Master index with embeddings
│   ├── entries/                      # Individual skill entries
│   │   ├── 2026/
│   │   │   ├── 06/
│   │   │   │   ├── skill-2026-06-10-01a2b3.yaml
│   │   │   │   └── skill-2026-06-10-04c5d6.yaml
│   │   │   └── 05/
│   │   └── 2025/
│   ├── patterns/                     # Extracted reusable patterns
│   │   ├── mcp-timeout-pattern.yaml
│   │   └── async-error-handling.yaml
│   └── queries/                      # Common query templates
│       └── "how-do-i-handle-mcp-timeouts.yaml"
│
├── knowledge/
│   └── projects/
│       └── skill-journal-research.md  # This document
│
├── fleet_kb.md                        # Links to relevant skills
└── commitments/                       # Decisions that led to skills
```

### 4.2 Index Structure

The index enables fast lookup by pattern/tag/domain:

```yaml
# skill-journal/index.yaml
index_version: "1.0"
last_updated: "2026-06-10T10:00:00-04:00"

# By pattern (primary lookup)
patterns:
  "mcp-tool-timeout-handling":
    - skill_id: "skill-2026-06-10-a1b2c3"
      score: 0.95                           # Relevance/confidence
    - skill_id: "skill-2026-05-20-d4e5f6"
      score: 0.82

# By domain (browsing)
domains:
  "mcp":
    skills:
      - "skill-2026-06-10-a1b2c3"
      - "skill-2026-05-15-xyz789"
    subdomains:
      "timeout": ["skill-2026-06-10-a1b2c3"]

# By tool used
tools:
  "asyncio":
    - "skill-2026-06-10-a1b2c3"
    - "skill-2026-05-20-d4e5f6"

# By agent (provenance)
agents:
  "Woodhouse":
    skills: ["skill-2026-06-10-a1b2c3", ...]
    domains: ["mcp", "asyncio", "security"]

# Embeddings reference (for semantic search)
embeddings:
  model: "text-embedding-3-small"
  location: "gx10-lab"                    # Where embeddings stored/computed
  entries:
    "skill-2026-06-10-a1b2c3":
      vector_id: "vec_abc123"
      last_computed: "2026-06-10T10:00:00-04:00"
```

---

## 5. Query Interface

### 5.1 Natural Language Query

Agents ask questions in natural language:

```python
# Agent query
result = skill_journal.query(
    "Has anyone solved MCP timeout issues before?"
)
```

**Query Processing:**
1. Parse intent (lookup vs. browse vs. pattern match)
2. Extract keywords/entities
3. Check index for exact pattern match
4. Fall back to semantic search (embeddings)
5. Rank by relevance + recency + validation status
6. Return top-N with confidence scores

### 5.2 Structured Query

For programmatic access:

```python
# Pattern-based lookup
result = skill_journal.find_by_pattern(
    pattern="mcp-tool-timeout-handling"
)

# Domain browse
result = skill_journal.find_by_domain(
    domain="mcp",
    subdomain="timeout"
)

# Tool-based lookup
result = skill_journal.find_by_tools(
    tools=["asyncio", "tenacity"]
)

# Combined filter
result = skill_journal.query(
    filters={
        "domain": ["mcp", "async"],
        "tools": ["asyncio"],
        "status": "active",
        "verified": True
    },
    sort="recency"
)
```

### 5.3 Query Response Format

```yaml
query_result:
  query: "Has anyone solved MCP timeout issues before?"
  parsed_intent: "pattern_lookup"
  matches:
    - skill_id: "skill-2026-06-10-a1b2c3"
      title: "MCP Tool Timeout Handling with Circuit Breaker"
      match_score: 0.94
      match_type: "exact_pattern"
      summary: "Implemented asyncio.wait_for() wrapper with tenacity retry"
      agent: "Woodhouse"
      validated: true
      quick_fix: |
        @retry(stop=stop_after_attempt(3))
        async def call_with_timeout(func, timeout=30):
            return await asyncio.wait_for(func(), timeout=timeout)
    - skill_id: "skill-2026-05-20-d4e5f6"
      title: "Async Error Handling Patterns"
      match_score: 0.78
      match_type: "semantic_similarity"
      summary: "Generic patterns for async error boundaries"
      agent: "Woodhouse"
      validated: true
  
  recommendations:
    - "Use skill-2026-06-10-a1b2c3 — it's directly validated for MCP timeouts"
    - "Consider reviewing skill-2026-05-20-d4e5f6 for additional context"
  
  no_match_suggestions:
    - "Try rephrasing: 'mcp connection timeout'"
    - "Browse all MCP skills: /skill-journal/browse/mcp"
    - "Create a new skill entry from your solution"
```

---

## 6. Integration Points

### 6.1 Fleet-KB Integration

**Linking skills to projects:**

```markdown
<!-- In fleet_kb.md -->
## Project: Vigil

### Relevant Skills
- [MCP Timeout Handling](/skill-journal/entries/2026/06/skill-2026-06-10-a1b2c3.yaml)
- [Async Error Patterns](/skill-journal/entries/2026/05/skill-2026-05-20-d4e5f6.yaml)
```

**Skill entries reference projects:**

```yaml
# In skill entry
context:
  project: "Vigil"
  component: "mcp-client"
  related_kb: "memory/knowledge/projects/vigil-roadmap.md"
```

### 6.2 Commitments Integration

Skills often emerge from commitments:

```yaml
# In skill entry
provenance:
  derived_from_commitment: "dec-2026-05-17-002"
  context: "Research led to this implementation approach"
```

### 6.3 Mesh Memory (Cross-Agent)

**Sync protocol for cross-agent skill sharing:**

```yaml
# skill-journal/mesh-sync.yaml
mesh_sync:
  enabled: true
  share_with: ["Ray", "Liz"]
  
  # Skills tagged with "shared" are published to mesh
  publish_rules:
    - tag: "shared"
      auto_publish: true
    - status: "validated"
      auto_publish: true
  
  # Subscribe to skills from other agents
  subscriptions:
    - agent: "Ray"
      domains: ["commerce", "api-design"]
    - agent: "Liz"
      domains: ["ui", "design-systems"]
```

**Mesh skill entry (received from another agent):**

```yaml
skill_entry:
  id: "skill-ray-2026-06-09-xyz789"
  origin:
    agent: "Ray"
    mesh_node: "192.168.50.22"
    imported_at: "2026-06-10T11:00:00-04:00"
  
  # Same structure, but marked as imported
  status: "imported"  # local | imported | forked
  original_url: "ray://skill-journal/entries/2026/06/skill-xyz789.yaml"
```

### 6.4 Session Context Integration

**Auto-capture during sessions:**

When an agent solves a novel problem:

1. Agent detects "novel problem" (no existing skill match)
2. Agent solves it
3. Agent prompted: "Record this as skill? [Y/n]"
4. If yes → quick-capture form → draft skill entry
5. Agent can promote to full entry later

**Heartbeat skill review:**

```markdown
<!-- HEARTBEAT.md -->
## Periodic Tasks

- [ ] Review draft skill entries (promote/expire)
- [ ] Sync validated skills to mesh
- [ ] Update skill-journal index embeddings
```

---

## 7. Implementation Milestones

### Milestone 1: Local Skill Journal (Week 1)
**Goal:** Single agent can record and retrieve skills

- [ ] Create `memory/skill-journal/` directory structure
- [ ] Implement YAML schema validation
- [ ] Build simple CLI tool for CRUD operations
- [ ] Create 3-5 sample skill entries
- [ ] Implement pattern-based lookup

**Files:**
- `skill-journal/index.yaml`
- `skill-journal/entries/2026/06/*.yaml`
- `tools/skill_journal.py` (CLI)

### Milestone 2: Semantic Search (Week 2-3)
**Goal:** Natural language queries work

- [ ] Integrate with GX-10 for embeddings
- [ ] Build semantic similarity matching
- [ ] Hybrid search (pattern + semantic)
- [ ] Query result ranking

**Files:**
- `tools/skill_journal_query.py`
- Embedding sync to GX-10

### Milestone 3: Mesh Sharing (Week 4-5)
**Goal:** Skills flow between agents

- [ ] A2A protocol extension for skill sync
- [ ] Import/export with provenance tracking
- [ ] Conflict resolution (same problem, different solutions)
- [ ] Skill voting/rating between agents

**Files:**
- `skill-journal/mesh-sync.yaml`
- A2A message types for skill exchange

### Milestone 4: Auto-Capture (Week 6-8)
**Goal:** Skills capture without explicit action

- [ ] Detect novel problems automatically
- [ ] Suggest skill capture at solution time
- [ ] Extract patterns from code changes
- [ ] Link skills to git commits

**Files:**
- Integration with agent session lifecycle
- Git hooks for skill extraction

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Skill Retrieval Time | <2s | Average query latency |
| Query Precision | >80% | Relevant skills in top-3 |
| Coverage | >60% | Novel problems with matching skills |
| Reuse Rate | >40% | Skills accessed by agents other than creator |
| Cross-Agent Sharing | >20% | Skills imported from other agents |

---

## 9. Recommended Schema (Summary)

### Minimal Viable Skill Entry

```yaml
skill_entry:
  id: "skill-{timestamp}-{hash}"
  source:
    agent: "AgentName"
    timestamp: "2026-06-10T09:50:00-04:00"
  
  problem:
    pattern: "machine-readable-tag"
    description: "Human-readable problem statement"
    domain: ["tech", "area"]
  
  solution:
    approach: "High-level approach"
    steps: ["step 1", "step 2"]
  
  implementation:
    tools_used: ["tool1", "tool2"]
    code_snippet: "# Optional but valuable"
  
  lessons: ["What was learned"]
  gotchas: ["What went wrong"]
  
  tags: ["searchable", "tags"]
  status: "active"  # active | deprecated
```

### Storage Approach

1. **Local Files:** YAML in `memory/skill-journal/entries/YYYY/MM/`
2. **Index:** `memory/skill-journal/index.yaml` for fast lookups
3. **Embeddings:** Stored on GX-10, referenced by ID
4. **Mesh Sync:** A2A protocol extension for cross-agent sharing

### First Integration Milestone

**Milestone 1: Local Skill Journal (This Week)**

Deliverables:
1. ✅ Directory structure at `memory/skill-journal/`
2. ✅ YAML schema defined (see above)
3. ✅ CLI tool: `tools/skill_journal.py` with create/query commands
4. ✅ 3 sample entries demonstrating pattern
5. ✅ Integration test: Agent A records skill, Agent B retrieves it

Next Steps After M1:
- Deploy to Woodhouse/Ray/Liz mesh
- Collect usage data for semantic search priority
- Design A2A mesh sync protocol

---

*Document written by Woodhouse subagent for Agent Knowledge Persistence initiative.*
*Approved for implementation by Mr. Ross on 2026-06-10.*

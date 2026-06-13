# Context Capsule Research

## Research: Conversation Context Transfer for Agent-to-Agent Handoffs

### Executive Summary

Current subagent handoffs rely on text summaries that lose significant nuance—semantic intent, conversational state, emotional valence, and implicit context. This research explores a "Context Capsule" format that compresses conversation state densely but reversibly, preserving more of the original context than summaries allow.

---

## 1. Compression Strategies Analysis

### 1.1 Summarization (Current Approach)

**How it works:** Text compression via abstraction and condensation.

| Aspect | Detail |
|--------|--------|
| **Pros** | Human-readable, easy to implement, no special parsing needed |
| **Cons** | Lossy (semantic drift, nuance loss), variable length, no structure guarantees |
| **Token Efficiency** | Poor—10:1 to 20:1 compression, but high information loss |
| **Reversibility** | One-way; cannot reconstruct original intent |

**Pain Points:**
- Loses subtle user preferences mentioned early in conversation
- Drops "vibe" and emotional context
- Cannot capture partial/uncertain knowledge states
- Summaries grow stale quickly in multi-turn contexts

### 1.2 Embeddings (Vector Representation)

**How it works:** Dense vector representations of semantic meaning.

| Aspect | Detail |
|--------|--------|
| **Pros** | Captures semantic similarity, fixed-size, searchable, captures meaning not just words |
| **Cons** | Not directly interpretable, requires model to "understand" vectors, lossy reconstruction |
| **Token Efficiency** | Excellent—384-1536 dimensions = ~500-2000 tokens if serialized as text |
| **Reversibility** | Semantic only; exact details lost |

**Approaches:**
- **Single embedding** of full conversation
- **Hierarchical embeddings** (message-level + conversation-level)
- **Multi-aspect embeddings** (intent, entities, sentiment as separate vectors)

### 1.3 Structured Extraction (Key-Value)

**How it works:** Extract defined fields (entities, intents, preferences, state flags) into structured format.

| Aspect | Detail |
|--------|--------|
| **Pros** | Predictable schema, directly parseable, type-safe, verifiable |
| **Cons** | Schema brittleness, misses emergent/unexpected information |
| **Token Efficiency** | Good—compact when schema matches content |
| **Reversibility** | Partial—defined fields reversible, undefined content lost |

**Key Fields to Extract:**
```
- User intent (primary + secondary)
- Entities mentioned (with types and salience)
- Preferences stated (explicit + inferred)
- Conversation state (stage, pending questions)
- Emotional valence (sentiment, urgency, frustration)
- Knowledge gaps (what agent doesn't know)
- Action items (pending, completed, blocked)
- Style/tone preferences
```

### 1.4 Hybrid Approaches (Recommended)

**Strategy: Structured Core + Semantic Embeddings + Selective Verbatim**

```
┌─────────────────────────────────────────────────────────┐
│                    CONTEXT CAPSULE                       │
├─────────────────────────────────────────────────────────┤
│  HEADER (metadata, size, version)                       │
├─────────────────────────────────────────────────────────┤
│  STRUCTURED CORE (extracted facts, state, entities)      │
├─────────────────────────────────────────────────────────┤
│  SEMANTIC EMBEDDING (vector representation)              │
├─────────────────────────────────────────────────────────┤
│  VERBATIM SNIPPETS (critical quotes, exact wording)      │
├─────────────────────────────────────────────────────────┤
│  SUMMARY GAP (high-level narrative for quick context)    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Pain Points in Current Summary-Based Handoffs

### 2.1 Information Loss Categories

| Category | What's Lost | Impact |
|----------|-------------|--------|
| **Temporal Context** | When things were said, conversation flow | Agent can't reference "earlier" vs "just now" |
| **Epistemic State** | What agent knew when, confidence levels | May re-ask questions or assume knowledge |
| **Social/Emotional** | Tone shifts, rapport built, user frustration | Tone-deaf responses, rapport destruction |
| **Implicit Context** | Unstated assumptions, shared understanding | Misinterpretation of user intent |
| **Granular Details** | Exact quotes, specific numbers, precise wording | Revisions that drift from original intent |
| **Exploration History** | Branches considered and rejected | Repeated exploration, user frustration |
| **Tool/Action History** | What was tried, results, partial successes | Duplicate tool calls, wasted tokens |

### 2.2 Real Scenarios Where Summaries Fail

**Scenario 1: Technical Debugging**
- User describes error A, then mentions error B is related
- Summary: "User has errors A and B"
- Lost: Causality, sequence, user's theory about relationship
- Result: Subagent investigates independently, wasting time

**Scenario 2: Creative Collaboration**
- User rejects idea X, suggests Y with specific constraint Z
- Summary: "User prefers Y over X, wants constraint Z"
- Lost: Why X was rejected (matters for Y implementation), emotional investment in Z
- Result: Subagent misses critical subtext

**Scenario 3: Multi-Step Task**
- Step 1 done, Step 2 partially done with blocker, Step 3 identified
- Summary: "Task in progress, Step 2 has blocker"
- Lost: What was tried for Step 2, exact blocker nature, Step 3 dependencies
- Result: Subagent restarts Step 2 investigation

---

## 3. Context Capsule Format Design

### 3.1 Prototype Format: "CC-1" (Context Capsule v1)

**Design Principles:**
1. **Dense but parseable** — JSON-based with optional binary encoding
2. **Layered** — Different detail levels for different use cases
3. **Extensible** — Schema versioned, fields optional
4. **Token-conscious** — Prioritize high-signal fields
5. **Reversible** — Original intent reconstructable

```json
{
  "_cc": {
    "v": "1.0",
    "ts": "2026-06-10T09:50:00Z",
    "tok": 2847,
    "src": "agent:main:telegram:direct:8362390464"
  },
  "intent": {
    "primary": "debug_connection_issue",
    "secondary": ["understand_logs", "verify_config"],
    "confidence": 0.87,
    "evolved_from": "initial_complaint_about_slow_speed"
  },
  "user": {
    "pref": {
      "detail_level": "technical",
      "verbosity": "concise",
      "code_examples": true
    },
    "state": {
      "frustration": 0.3,
      "urgency": 0.8,
      "knowledge_level": "expert"
    },
    "mentioned": {
      "tools": ["curl", "wireshark", "tcpdump"],
      "systems": ["nginx", "cloudflare"],
      "constraints": ["cannot_restart_production"]
    }
  },
  "conversation": {
    "turns": 12,
    "duration_min": 8,
    "stage": "investigation",
    "pending_questions": ["what_changed_recently"],
    "blockers": ["missing_log_access"]
  },
  "actions": {
    "completed": [
      {"tool": "read_file", "file": "/var/log/nginx/error.log", "result": "success"},
      {"tool": "exec", "cmd": "curl -I https://example.com", "result": "timeout"}
    ],
    "attempted_failed": [
      {"intent": "check_firewall", "reason": "insufficient_privileges"}
    ],
    "planned": [
      {"tool": "exec", "cmd": "traceroute example.com"}
    ]
  },
  "knowledge": {
    "confirmed": {
      "timeout_occurs": true,
      "affects_https_only": true,
      "started_2_days_ago": true
    },
    "inferred": {
      "likely_cdn_issue": 0.7,
      "possible_cert_problem": 0.4
    },
    "unknown": [
      "recent_deployment_history",
      "upstream_health_status"
    ]
  },
  "semantic": {
    "embedding_b64": "base64_encoded_vector...",
    "dim": 768,
    "model": "text-embedding-3-small"
  },
  "verbatim": {
    "critical_quotes": [
      {"speaker": "user", "text": "This started exactly 2 days ago, right after the maintenance window", "importance": 0.95},
      {"speaker": "agent", "text": "I'll check the certificate validity", "importance": 0.7}
    ],
    "exact_values": {
      "timeout_seconds": "30",
      "error_code": "524",
      "affected_urls": ["/api/v1/sync", "/api/v2/batch"]
    }
  },
  "narrative": "User reports HTTPS timeouts on specific API endpoints starting 2 days ago. Initial investigation shows 524 errors from Cloudflare. User mentioned maintenance window timing—likely related. Cannot access firewall logs. Needs traceroute and cert check."
}
```

### 3.2 Field Priorities for Token-Limited Scenarios

When token budget is tight, drop in this order:

1. **Keep (Critical):** `intent.primary`, `user.state`, `knowledge.confirmed`, `verbatim.exact_values`
2. **Keep if space:** `actions.completed`, `conversation.stage`, `verbatim.critical_quotes`
3. **Drop first:** `narrative`, `semantic.embedding`, `actions.planned`, `intent.secondary`

### 3.3 Size Estimates

| Component | Approx Tokens |
|-----------|---------------|
| Header + metadata | 50 |
| Structured core (intent, user, conversation) | 200-400 |
| Actions (10 items) | 150-300 |
| Knowledge (confirmed + inferred + unknown) | 100-200 |
| Verbatim quotes (3-5 critical) | 100-200 |
| Semantic embedding (base64, 768 dim) | ~400 |
| Narrative summary | 50-100 |
| **Total (full capsule)** | **~1000-1800 tokens** |
| **Total (compressed, no embedding)** | **~600-1100 tokens** |
| **Total (minimal)** | **~300-500 tokens** |

---

## 4. Decompression/Rehydration Approach

### 4.1 Rehydration Strategy

The receiving agent must "rehydrate" the capsule into working context:

**Step 1: Schema Validation**
- Verify version compatibility
- Check for required fields
- Report missing optional fields

**Step 2: Intent Reconstruction**
- Primary intent becomes system prompt directive
- Confidence level adjusts agent's assertiveness
- Evolution tracking prevents regression

**Step 3: User Model Loading**
- Preferences inform response generation
- State (frustration/urgency) adjusts tone
- Knowledge level sets explanation depth

**Step 4: Conversation State Restoration**
- Stage determines available actions
- Pending questions are prioritized
- Blockers constrain options

**Step 5: Knowledge Graph Integration**
- Confirmed facts = working assumptions
- Inferred facts = hypotheses to verify/mention
- Unknowns = explicit information gaps

**Step 6: Verbatim Injection**
- Critical quotes available for exact reference
- Exact values used for precision

**Step 7: Semantic Alignment (optional)**
- If receiving agent supports embeddings:
  - Decode embedding
  - Compare with current conversation embedding
  - Flag semantic drift if divergence > threshold

### 4.2 Prompt Template for Rehydration

```
You are continuing a conversation in progress. The following context capsule 
contains the state of the conversation at handoff.

CONVERSAL STATE:
- Primary intent: {intent.primary}
- User knowledge level: {user.state.knowledge_level}
- Current frustration: {user.state.frustration}/1.0
- Conversation stage: {conversation.stage}
- Pending questions: {conversation.pending_questions}

CONFIRMED FACTS (treat as true):
{knowledge.confirmed}

INFERENCES (may need verification):
{knowledge.inferred}

CRITICAL QUOTES:
{verbatim.critical_quotes}

EXACT VALUES:
{verbatim.exact_values}

ACTIONS ALREADY TAKEN:
{actions.completed}

NARRATIVE: {narrative}

Continue the conversation naturally, respecting the user's preferences and 
current state. Do not re-ask questions already answered or re-attempt actions 
already completed.
```

---

## 5. Token Efficiency vs Information Fidelity Tradeoffs

### 5.1 Comparison Matrix

| Approach | Tokens | Fidelity | Reversibility | Best For |
|----------|--------|----------|---------------|----------|
| Text Summary (current) | 200-500 | Low | None | Simple, single-turn tasks |
| Minimal Capsule | 300-500 | Medium | Partial | Token-constrained scenarios |
| Standard Capsule | 600-1100 | High | Strong | Standard handoffs |
| Full Capsule + Embedding | 1000-1800 | Very High | Semantic | Complex, multi-stage tasks |
| Full Conversation | 2000-10000+ | Perfect | Perfect | When tokens allow |

### 5.2 Decision Tree

```
Is task simple (< 3 turns, no ambiguity)?
├── YES → Use text summary
└── NO → Does parent have embedding support?
    ├── YES → Include semantic embedding
    └── NO → Skip embedding, use structured only
        └── Token budget < 1000?
            ├── YES → Minimal capsule
            └── NO → Standard capsule
```

---

## 6. Integration with OpenClaw Subagent Patterns

### 6.1 Current Subagent Handoff

```
Parent Agent:
  ↓ Spawns subagent with "context" string
Subagent:
  ↓ Receives text summary only
```

### 6.2 Proposed Context Capsule Integration

```
Parent Agent:
  ↓ Builds capsule from conversation state
  ↓ Encodes as JSON (or compressed binary)
  ↓ Spawns subagent with capsule
Subagent:
  ↓ Receives capsule
  ↓ Rehydrates into working context
  ↓ Continues conversation
  ↓ Returns capsule with updates (optional)
Parent Agent:
  ↓ Receives updated capsule
  ↓ Merges with current state
```

### 6.3 Implementation Path

**Phase 1: Structured JSON (Minimal)**
- Add optional `context_capsule` field to subagent spawn
- Support basic schema (intent, user preferences, conversation state)
- Backwards compatible (falls back to summary)

**Phase 2: Full Capsule**
- Add verbatim tracking for critical quotes
- Add action history (completed, failed, planned)
- Add knowledge graph (confirmed, inferred, unknown)

**Phase 3: Semantic Layer**
- Integrate embedding generation (optional dependency)
- Add semantic drift detection
- Support capsule merging/composition

**Phase 4: Optimization**
- Binary encoding for size reduction
- Compression (gzip/brotli for large capsules)
- Selective field population based on task type

---

## 7. Recommendations

### 7.1 Recommended Capsule Format

**Use: Hybrid Structured + Selective Verbatim (CC-1)**

**Rationale:**
- Structured fields ensure key information is captured predictably
- Verbatim quotes preserve precision where exact wording matters
- Avoids embedding complexity in Phase 1
- JSON ensures portability and readability
- Token cost (~600-1100) is reasonable for meaningful context preservation

### 7.2 Recommended Compression Strategy

**Tiered approach based on task complexity:**

| Task Type | Strategy |
|-----------|----------|
| Simple lookup | Text summary only |
| Standard task | Minimal capsule (intent + state + verbatim) |
| Complex investigation | Standard capsule (full structured, no embedding) |
| Research/analysis | Full capsule with embedding |

**Smart truncation:**
- Always keep `intent.primary`, `user.state`, `knowledge.confirmed`
- Prioritize recent actions over older ones
- Keep verbatim quotes with highest importance score

### 7.3 First Prototype Target

**Target: Minimal Viable Capsule for OpenClaw**

**Scope:**
1. Define JSON schema for CC-1 Minimal (intent, user state/preferences, conversation stage, verbatim quotes)
2. Implement capsule builder in parent agent (extract from conversation)
3. Implement rehydration in subagent prompt template
4. Test on: technical debugging, creative writing, multi-step tasks
5. Measure: user satisfaction, task completion rate, token overhead

**Success Criteria:**
- Subagent can continue conversation without re-asking answered questions
- Critical details (exact values, specific constraints) are preserved
- Token overhead < 50% of original conversation length
- Backwards compatible (works alongside existing summary system)

---

## 8. Open Questions

1. **Capsule lifetime:** Should capsules persist beyond immediate handoff? Enable async workflows?
2. **Merging capsules:** How to combine multiple child capsules back to parent?
3. **Embedding model:** Which embedding model provides best cost/quality for context similarity?
4. **Security:** Capsules may contain sensitive data—encryption at rest/in transit?
5. **Versioning:** How to evolve schema without breaking older capsules?

---

## 9. References & Inspiration

- **LangChain Memory Systems** — ConversationBufferMemory, ConversationSummaryMemory
- **Anthropic's Context Caching** — Efficient context preservation patterns
- **Research: "MemGPT"** — Virtual context management for LLMs
- **Research: "Compressing Context for Efficient LLM Inference"** — Various compression approaches
- **OpenAI's Structured Outputs** — JSON schema enforcement for reliability

---

*Document created: 2026-06-10*
*Research phase: Initial design*
*Next step: Prototype implementation and testing*

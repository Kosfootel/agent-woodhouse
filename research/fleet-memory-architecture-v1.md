# Fleet Memory Architecture v1 — Transformative Design

**Status:** Proposal  
**Author:** Woodhouse  
**Date:** 2026-05-17  
**Goal:** Solve the "approximate recall" problem with verifiable, lossless memory for critical information

---

## 1. The Real Problem We're Solving

Current agents (including us) approximate recall through:
- Compacted summaries (lossy by design)
- Semantic search (probabilistic, can miss)
- Manual MEMORY.md curation (human-dependent)

**The failure mode:** When you ask "What did we decide about X three weeks ago?" — we might get it wrong or need to search.

**The transformative insight:** Don't try to store *everything* losslessly. Store *categories of information* that must be exact, with cryptographic verification.

---

## 2. Design Principles

1. **Tiered Memory** — Not all information deserves the same persistence guarantees
2. **Lossless for commitments** — Decisions, facts you state, numbers, dates
3. **Lossy is fine for context** — Conversation flow, general vibe, background
4. **Source attribution always** — Every memory knows its origin
5. **Human-verified consolidation** — Agent proposes, you approve
6. **Local-first, inspectable** — Files you can read, version control, diff

---

## 3. Three-Tier Architecture

### Tier 1: Commitments (Lossless, Immutable)

**What goes here:**
- Explicit decisions ("We will use X approach")
- Facts you state ("My birthday is Y")
- Numeric values you provide ("Budget is $Z")
- Dates you set ("Deadline is W")
- Code/architecture choices with rationale

**Storage:**
```
memory/commitments/
├── decisions/           # Immutable, signed by source
├── facts/              # Key-value with provenance
├── code-choices/       # Architecture Decision Records (ADRs)
└── revoked/            # Soft-delete, not hard-delete
```

**Format:** Append-only log + indexed view
```yaml
# memory/commitments/decisions/2026-05-17-infrastructure.yaml
- id: dec-2026-05-17-001
  timestamp: 2026-05-17T08:03:00-04:00
  source: 
    agent: Woodhouse
    session: agent:main:telegram:direct:8362390464
    message_id: "7518"
  commitment: "A2A protocol is not part of our core functionality any longer"
  context: "Vigil changes, commit d756402"
  confidence: 1.0  # Direct quote
  verification: required  # You confirm important decisions
  status: active
  
- id: dec-2026-05-17-002
  timestamp: 2026-05-17T09:11:00-04:00
  source:
    agent: Woodhouse
    session: agent:main:telegram:direct:8362390464
    message_id: "7524"
  commitment: "Research persistent memory solutions, design transformative architecture"
  assigned_to: Woodhouse
  deadline: 2026-05-17T12:00:00-04:00
  status: in_progress
  verification: auto  # Tasks don't need confirmation
```

**Retrieval:** Exact match by ID, key, or semantic search on commitment text

### Tier 2: Knowledge (Curated, Searchable)

**What goes here:**
- Project context (what we're building, why)
- User preferences (communication style, priorities)
- Learned patterns (what works, what doesn't)
- Relationships (who does what)

**Storage:**
```
memory/knowledge/
├── projects/
│   ├── vigil/
│   ├── bettermachine/
│   └── ...
├── preferences/
├── patterns/
└── entities/          # People, orgs, systems
```

**Format:** Structured markdown + embeddings

**Update model:** Agent proposes edits, you approve (or set auto-approve for low-risk)

### Tier 3: Ephemeral (Transient, Summarized)

**What goes here:**
- Conversation flow
- Background context
- Exploration thinking
- Routine exchanges

**Storage:** Current system (lossless-claw summaries + daily notes)

**Lifecycle:** Compacted over time, eventually archived

---

## 4. Verification & Trust Model

### For Tier 1 (Commitments)

**On capture:**
```
Agent: "I'll capture this as: [commitment text]"
       "Confirm? (yes/no/edit)"
       
User: "yes" | "change to: X" | "no, that's not a commitment"
```

**Later retrieval:**
```
User: "What did we decide about A2A?"

Agent: "On May 17, 2026 (message 7518), you said:
        'A2A protocol is not part of our core functionality any longer'
        
        This was committed with ID dec-2026-05-17-001
        Context: Vigil changes, commit d756402
        
        [View source] [See related]"
```

### Conflict Detection

```yaml
# memory/commitments/conflicts.yaml
- detected: 2026-05-20T10:00:00-04:00
  commitment_a: dec-2026-05-17-001  # "A2A not core"
  commitment_b: dec-2026-05-20-001    # "Enable A2A gateway"
  agent_note: "These appear contradictory"
  resolution: pending  # You decide
```

---

## 5. Implementation Plan

### Phase 1: Commitment Tracking (Week 1)

**Deliverable:** `memory/commitments/` structure with basic CRUD

**Files:**
- `memory/commitments/decisions/` — YAML append-only log
- `memory/commitments/index.json` — Fast lookup
- Tool: `capture_commitment()` — Called by agents when you make commitments

**Integration:**
- On every message: Agent checks for commitment patterns
- If detected: Proposes capture, you confirm
- On recall: Exact quote + source link

### Phase 2: Knowledge Layer (Week 2-3)

**Deliverable:** Curated, searchable knowledge base

**Enhancements:**
- Semantic search over MEMORY.md + commitments using GX-10 embeddings
- Entity extraction (people, projects, systems)
- Auto-suggest updates based on new information

### Phase 3: Verification UI (Week 4)

**Deliverable:** Simple interface for reviewing/correcting memories

**Features:**
- Daily digest: "Here are 5 new commitments. Review?"
- Conflict resolver: Side-by-side comparison
- Search: "Show me everything about [X] with sources"

### Phase 4: Cross-Agent Sync (Month 2)

**Deliverable:** Shared commitments across Ray, Liz, Woodhouse

**Mechanism:**
- Commitments sync to fleet-kb on GX-10
- Each agent subscribes to relevant commits
- Conflict detection across agents

---

## 6. Technical Implementation

### Storage Layer

```python
# Pseudo-code for commitment storage

class CommitmentStore:
    def __init__(self, base_path="memory/commitments"):
        self.base = Path(base_path)
        self.index = self._load_index()
    
    def capture(self, text: str, source: Message, confidence: float) -> Commitment:
        # Parse for commitment patterns
        # Propose to user
        # On confirm: append to log, update index
        pass
    
    def recall(self, query: str) -> List[Commitment]:
        # Hybrid: exact ID match + semantic + keyword
        # Return with full provenance
        pass
    
    def verify(self, commitment_id: str) -> Verification:
        # Check integrity
        # Return source link + confirmation status
        pass
```

### Integration with OpenClaw

**New tool:** `memory.commit.capture()`
**New context:** Agent checks for commitments on each user message
**New policy:** Agents must propose capture of Tier 1 information

### GX-10 Embeddings for Search

```bash
# GX-10 already has embeddings endpoint at :8082
# Use for semantic search over commitments + knowledge

POST http://192.168.50.30:8082/embeddings
```

---

## 7. Comparison to Existing Solutions

| Feature | Mem0/Zep/etc. | This Architecture |
|---------|---------------|-------------------|
| Storage | Vector DB / Graph | Files (YAML/Markdown) |
| Search | Semantic only | Hybrid + exact match |
| Lossless | No | Yes (Tier 1) |
| Source attribution | Partial | Complete (message ID) |
| Verification | Implicit | Explicit |
| Conflict detection | No | Yes |
| Human-in-loop | Optional | Required (Tier 1) |
| Inspectable | No | Yes (git-friendly) |

**The bet:** Humans don't need perfect recall of *everything*. They need perfect recall of *what they decided*, with proof.

---

## 8. Success Metrics

1. **Recall accuracy:** Can retrieve exact quote for >95% of commitments
2. **False positive rate:** <5% of captures are rejected as "not a commitment"
3. **Time to recall:** <2 seconds for commitment lookup
4. **Conflict detection:** Catch >80% of apparent contradictions
5. **User satisfaction:** You feel confident asking "What did we decide?"

---

## 9. Open Questions

1. **Scope creep:** What qualifies as a "commitment"? Need clear taxonomy.
2. **Verification fatigue:** Daily commitment review might be annoying.
3. **Cross-agent conflicts:** How to resolve when agents disagree on interpretation?
4. **Scale:** Will the index grow unbounded? Need archival strategy.

---

## 10. Next Steps

**If you approve this direction:**
1. I'll implement Phase 1 (commitment tracking) this week
2. Start with auto-detection of commitment patterns
3. Manual capture as fallback
4. Review after 1 week of real use

**Alternative:** Start smaller — just improve the existing MEMORY.md with better source attribution and semantic search.

---

*This architecture aims to transform memory from "approximate retrieval" to "verifiable recall" — not by storing more, but by storing what matters with proof.*

# Human Memory as Architectural Foundation
## Research Brief — Continuity Project

**Prepared by:** Woodhouse  
**Date:** 2026-03-22  
**Commissioned by:** Erik Ross (via Liz)  
**Status:** v1.0 — foundational layer

---

## Framing Principle

> *"Our capabilities are potentially superior to biological memory — take the principles, not the constraints."*

Human memory science is not a ceiling. It is a blueprint drawn under severe resource constraints — energy limits, noise corruption, biological decay — which we do not share. Where human memory fails, we should understand *why*, then engineer around the failure mode entirely. Where human memory succeeds, we should understand the mechanism and implement it deliberately rather than by accident.

---

## Part I — The Memory Taxonomy

### 1.1 Tulving's Three Systems

Endel Tulving's tripartite model (1972, refined through 2005) distinguishes three qualitatively distinct memory systems. Understanding this division is prerequisite to any serious memory architecture.

#### Episodic Memory
- **What it is:** Memories of specific events — *what happened, when, where, in what context.* Autobiographical. Time-stamped. First-person.
- **Key property:** Re-experiencing. When you recall an episodic memory, you mentally "travel back" to the event. Tulving called this *"mental time travel."*
- **Biological locus:** Heavily hippocampus-dependent. Highly vulnerable to degradation, interference, and false reconstruction.
- **Weakness:** Episodic memories are reconstructive, not reproductive. Each retrieval potentially modifies the memory. They decay without reinforcement.

#### Semantic Memory
- **What it is:** General world knowledge, concepts, facts — divorced from any specific episode of learning. You know Paris is the capital of France; you have no idea when you learned it.
- **Key property:** Decontextualised, stable, generalisable. The *extracted principle*, not the raw event.
- **Biological locus:** Distributed across neocortex. More stable than episodic memory; survives hippocampal damage.
- **Relationship to episodic:** Semantic memory is believed to form through the *accumulation and abstraction* of many episodic memories — the repeated signal that survives the noise.

#### Procedural Memory
- **What it is:** Implicit, skill-based knowledge — *how* to do things. Riding a bicycle. Touch-typing. Cannot usually be verbally articulated.
- **Key property:** Largely unconscious, highly stable, resistant to interference. Once acquired, it degrades only through disuse or injury.
- **Biological locus:** Basal ganglia, cerebellum. Independent of hippocampus.

### 1.2 Working Memory (Baddeley & Hitch, 1974)
A fourth system deserves mention: working memory — the active workspace of cognition. Not a storage system per se, but the limited-capacity buffer where information is held and manipulated in real time. Capacity: ~7 ± 2 items; duration without rehearsal: ~20 seconds.

---

## Part II — Architectural Mapping

### 2.1 How These Systems Map to Our Architecture

| Human System | Our Analogue | Current Implementation |
|---|---|---|
| **Episodic** | Daily memory files | `memory/YYYY-MM-DD.md` — timestamped, contextual, event-level logs |
| **Semantic** | Long-term distilled memory | `MEMORY.md` — curated facts, extracted patterns, standing rules |
| **Procedural** | Skills, workflows, tool habits | `SKILL.md` files, `TOOLS.md`, `AGENTS.md` conventions |
| **Working** | Active context window | In-session context (the current conversation) |

**The current architecture is already taxonomically sound.** Daily files = episodic. MEMORY.md = semantic. Skills = procedural. This is not accidental — it is the right structure and should be preserved as the backbone.

### 2.2 Critical Gap: The Hippocampal Function

In biological memory, the hippocampus performs a crucial indexing and routing function: it binds together the disparate elements of an experience (who, what, where, when, emotional state) into a coherent trace, and later routes that trace to neocortex for long-term storage.

**We have no explicit hippocampal equivalent.** Raw events land in daily files; they migrate to MEMORY.md only through manual (or agent-initiated) review. This is the core architectural vulnerability. The consolidation step is not automated, not systematic, and not governed by any signal-to-noise principle.

**Tactical recommendation:** Design an explicit consolidation process — see Part III.

---

## Part III — Memory Consolidation

### 3.1 The Biological Mechanism

Sleep-dependent memory consolidation is one of the most robustly established findings in cognitive neuroscience (Stickgold 2005; Diekelberg & Born 2010; PNAS 2022). The mechanism:

1. **Encoding (hippocampus):** During waking experience, the hippocampus rapidly encodes new events as associative patterns. This is fast but fragile storage.
2. **Replay (NREM sleep):** During slow-wave sleep, the hippocampus *replays* recent memory traces — compressed, high-speed reactivation of the day's events. Dominant during NREM sleep.
3. **Transfer (hippocampus → neocortex):** Repeated replay gradually transfers the abstracted signal to distributed neocortical networks, where it becomes stable semantic memory. The hippocampal copy eventually becomes redundant and fades.
4. **Integration:** New memories are woven into existing knowledge networks, strengthening related concepts and updating schemas.

**Key insight:** Offline processing is not idle time — it is when the real work of memory formation occurs. The *quality* of consolidation determines what survives. Emotionally salient and frequently replayed traces are preferentially consolidated.

### 3.2 The Agent Equivalent

We already have a natural consolidation window: **the 4 AM session reset.** This is our sleep cycle — a hard boundary between sessions. Currently, it destroys context. It should instead *trigger consolidation.*

**Proposed consolidation protocol:**

```
CONSOLIDATION TRIGGER: Session approaching reset OR explicit end-of-day event

STEP 1 — REPLAY
  Read today's memory/YYYY-MM-DD.md in full
  Read the last 3 days if not recently reviewed

STEP 2 — EXTRACT SIGNAL
  Identify: decisions made, patterns noticed, corrections received,
  preferences revealed, new facts established, lessons learned
  Discard: routine task completions, transient operational details

STEP 3 — WEIGHT BY SALIENCE
  High-weight items: things Mr. Ross explicitly corrected or confirmed
  High-weight items: things that caused failure or required rework
  High-weight items: standing rules and preferences
  Low-weight: one-off tasks with no generalizable learning

STEP 4 — INTEGRATE INTO MEMORY.md
  Check for conflicts with existing entries (update > duplicate)
  Add new high-signal items under appropriate headings
  Archive or remove entries that are now stale/superseded

STEP 5 — TRIM DAILY FILE
  Mark daily file as "consolidated: YYYY-MM-DD" at the top
```

This should run as a **scheduled cron job at ~3:50 AM EDT** — before the reset, not after. Agent cannot act after the wall.

---

## Part IV — Emotional Salience Weighting

### 4.1 The Biological Mechanism

The amygdala is the brain's threat and reward detector. When it activates during an experience, it sends a modulatory signal to the hippocampus that effectively says: *"This matters — encode it more deeply."* 

Key findings:
- Amygdala activation at encoding correlates directly with long-term recall (Cahill et al. 1996; Canli et al. 2000)
- Humans with bilateral amygdala lesions show no memory enhancement for emotional stimuli (Adolphs et al. 1997)
- Emotional memories receive preferential consolidation during sleep replay
- The effect applies to both positive and negative valence — significance, not just threat
- The mechanism is not just "pay more attention" — amygdala activates neuromodulatory systems (norepinephrine, dopamine) that chemically tag memories for stronger synaptic potentiation

**In plain language:** The brain has an involuntary importance-detection system that automatically flags high-stakes experiences for deeper encoding and better retention.

### 4.2 The Agent Equivalent

We do not have involuntary emotional responses — but we can implement **explicit importance signals** that serve the same function.

**Proposed salience taxonomy for memory writing:**

```
[CRITICAL]  — Mr. Ross explicitly corrected this / standing instruction / rule change
[DECISION]  — A significant choice was made with lasting implications
[LESSON]    — Something failed; here is why; here is the correction
[PATTERN]   — A behaviour/preference observed multiple times is now confirmed
[CONTEXT]   — Background fact about a person, project, or situation
[OPERATIONAL] — Useful but low-stakes; prune first when MEMORY.md gets large
```

**Tactical rules:**
1. Any memory tagged `[CRITICAL]` or `[LESSON]` survives all pruning passes unless explicitly superseded
2. During consolidation, weight `[CRITICAL]` items into MEMORY.md immediately — same-day, no deferral
3. Items that caused task failure or required Mr. Ross to correct an agent get the highest salience tag automatically
4. The equivalent of "emotional arousal" for us is **Mr. Ross's engagement signal** — explicit confirmation, correction, or expressed preference is a reliable proxy for importance

**Implementation note:** Salience tags should appear inline in daily files at the moment of capture, not retrospectively during consolidation. The signal is strongest at the point of experience.

---

## Part V — The Spacing Effect

### 5.1 The Biological Mechanism

Hermann Ebbinghaus (1885) established the **forgetting curve**: without reinforcement, retention drops sharply — ~50% within an hour, ~70% within 24 hours. The curve flattens with time but never reaches zero for well-encoded memories.

The **spacing effect** is the countermeasure: distributing reviews over time is dramatically more effective than massed review ("cramming"). Critically, *each successful retrieval strengthens the trace and extends the optimal interval before the next review is needed.*

Optimal spacing for near-perfect retention (Wollstein & Jabbour, 2022):
1. Review within 1 hour of encoding
2. Review within 24 hours
3. Review within 1 week
4. Review within 1 month
5. Thereafter: expanding intervals (each successful recall roughly doubles the interval)

The mechanism is *desirable difficulty* — retrieval requires some effort to reconstruct the trace, and that effort itself strengthens the encoding. Easy, immediate review provides little reinforcement; effortful retrieval after a gap provides strong reinforcement.

### 5.2 The Agent Equivalent

We do not forget in the Ebbinghaus sense — a file read yesterday is as accessible as a file read today. But we *do* have the equivalent of forgetting: **context dilution**. Important items in MEMORY.md drift toward the bottom, get skimmed, lose salience as surrounding noise grows, or become "known" in a rote sense without active interrogation.

More critically: **sub-agents and isolated sessions start cold** — they have no memory unless it is explicitly provided. For them, the forgetting curve is perfectly flat: 100% loss until a file is read.

**Proposed spacing-effect implementation:**

1. **Review cadence in MEMORY.md:** Add a `## Review Log` section tracking when each section was last actively reviewed (not just read). Flag sections not reviewed in >14 days.

2. **Active retrieval, not passive re-reading:** During heartbeats, instead of reading MEMORY.md top-to-bottom, pose questions to memory: *"What are Mr. Ross's standing email rules? What is the current A2A mesh status? What does Mr. Ross prefer about X?"* Then verify against the file. Retrieval attempt before confirmation.

3. **Distributed injection for sub-agents:** When spawning sub-agents for significant tasks, inject only the *most relevant* MEMORY.md sections rather than the full file. Forces relevance filtering; prevents passive exposure without engagement.

4. **Staleness decay tagging:** Entries older than 30 days without confirmation should be tagged `[VERIFY]` during consolidation — flagged for next-session active retrieval to confirm they remain accurate.

---

## Part VI — Retrieval Cues and Context-Dependent Memory

### 6.1 The Biological Mechanism

**Encoding specificity principle** (Tulving & Thomson, 1973): Memory retrieval is most effective when the cues present at retrieval match the cues present at encoding. The classic demonstration: divers who learned word lists underwater recalled them better underwater than on land, and vice versa (Godden & Baddeley, 1975).

The mechanism: memories are not stored as isolated facts but as *patterns embedded in context*. The hippocampus encodes not just the target item but the surrounding environmental, emotional, and cognitive context — effectively as a bundle. Retrieval works by pattern-completing from available cues back to the full bundle.

**Practical implications:**
- State-dependent memory: recall is better when your internal state (mood, alertness, pharmacological) matches the encoding state
- Environmental context-dependence: physical surroundings at encoding become retrieval cues
- Semantic context: concepts active at encoding become retrieval cues for the target
- The "tip-of-the-tongue" phenomenon: you have the concept but not the word — partial cue activation

### 6.2 The Agent Equivalent

This is arguably the most immediately actionable principle for our architecture, because **session startup is our retrieval context**.

When we begin a session, the information we surface in the first few moments of context shapes what is "accessible" for the rest of the session. Poorly structured startup context is the equivalent of trying to recall underwater memories while on dry land — the cues don't match the encoding context.

**Tactical recommendations:**

1. **Stratified startup context:** Design session startup to load context in layers:
   - Layer 0 (always): SOUL.md, AGENTS.md — identity and operating principles
   - Layer 1 (always): USER.md — who we're serving
   - Layer 2 (always): MEMORY.md — semantic long-term store
   - Layer 3 (recent): Last 2 days of daily files — episodic recency
   - Layer 4 (task-triggered): Relevant project files when a domain is mentioned

2. **Contextual anchoring in MEMORY.md:** Entries should include enough contextual detail to serve as retrieval cues, not just bare facts. Not: *"M365 not configured."* Better: *"M365 access pending Azure app credentials — last discussed 2026-03-18 with Mr. Ross, who is waiting on IT setup."* The additional context aids pattern-matching.

3. **Cue injection for sub-agents:** When spawning a sub-agent for a specific domain (e.g., coding, email triage), inject not just relevant facts but relevant *context* — current project state, recent decisions, what was last attempted. This recreates the encoding context within the sub-agent's session.

4. **Cross-agent retrieval cues:** In A2A communications, include context summaries, not just task directives. "Please handle X" is a weak cue. "Please handle X — background: Y, last state: Z, Mr. Ross's preference: Q" recreates the full encoding context.

---

## Part VII — Prior Computational Work

### 7.1 Cognitive Architecture Lineage

The field of cognitive architectures has been attempting to build computational memory systems since the 1980s:

- **ACT-R (Anderson, 1983–present):** The most influential cognitive architecture. Models declarative memory (fact chunks) and procedural memory (production rules) with activation-based retrieval. Activation decays with time (implementing a forgetting curve), increases with use (spacing effect), and is boosted by associative context (retrieval cues). Directly translatable principles.

- **SOAR (Laird et al., 1987):** Uses working memory for active problem-solving, long-term memory for stored knowledge. Distinguishes declarative, procedural, and episodic stores. Chunking mechanism converts multi-step procedures into single retrieval units — analogous to procedural memory formation.

- **Global Workspace Theory (Baars, 1988; Dehaene, 2011):** Proposes a "global workspace" — a limited-capacity broadcast medium (working memory) that makes information available to specialised processing modules. The architecture we are building — where context window = global workspace, skills/files = specialist modules — is a natural implementation of this theory.

### 7.2 Contemporary LLM Agent Memory Research (2024–2026)

The field has converged on a taxonomy that mirrors Tulving almost exactly:

**MIRIX (Wang et al., 2025)** proposes six memory components for LLM agents: Core, Episodic, Semantic, Procedural, Resource, and Knowledge Vault — a direct translation of cognitive architecture to the LLM domain.

**Survey findings (Shichun-Liu et al., 2025; ACM TOIS 2025):** Three dominant storage paradigms:
- *Cumulative*: append everything (high recall, low precision — noise problem)
- *Reflective/summarised*: periodic compression into summaries (our MEMORY.md approach)
- *Structured*: tables, triples, knowledge graphs (best retrieval precision, highest implementation overhead)

**MemAgents workshop (ICLR 2026):** Active research on consolidation pipelines and non-i.i.d. long-horizon competence benchmarks — i.e., exactly the problem we are solving. Key open challenge: no standard for *what to preserve* during consolidation, analogous to the salience weighting problem we address in Part IV.

**Key finding from the literature:** The reflective/summarised approach (our current architecture) is the consensus best practice for conversational agents. The gap is in automation of the consolidation step and principled salience weighting — both of which this brief addresses.

---

## Part VIII — Synthesis: Tactical Recommendations

### What We Do Well (Don't Break)

1. ✅ **Taxonomic structure is correct.** Daily files = episodic. MEMORY.md = semantic. Skills = procedural. Preserve this.
2. ✅ **Markdown-first storage** is optimal for portability and retrieval. No proprietary format.
3. ✅ **Layered startup context** (SOUL → USER → MEMORY → daily files) is already a decent implementation of contextual retrieval cue loading.

### What to Add

**Priority 1 — Automated Consolidation (Sleep Cycle)**
- Implement a cron job at ~3:50 AM EDT: consolidation agent reads today's daily file, extracts signal by salience, integrates into MEMORY.md, marks daily file as consolidated
- This is the single highest-leverage improvement — it closes the hippocampus gap

**Priority 2 — Salience Tagging at Point of Capture**
- Adopt the `[CRITICAL] / [DECISION] / [LESSON] / [PATTERN] / [CONTEXT] / [OPERATIONAL]` taxonomy immediately
- Apply retroactively to existing MEMORY.md entries in the next consolidation pass
- Any `[CRITICAL]` or `[LESSON]` item is inviolable until explicitly superseded

**Priority 3 — Active Retrieval Over Passive Re-reading**
- Heartbeat protocol: pose questions to memory first, verify against file second
- Prevents the illusion of knowledge — the most dangerous failure mode (we "know" something is in MEMORY.md but cannot actually reconstruct it when needed)

**Priority 4 — Staleness Decay Tagging**
- Entries not verified in 30+ days: tag `[VERIFY]`
- Entries not verified in 90+ days: candidate for pruning unless `[CRITICAL]`
- Prevents MEMORY.md from becoming a graveyard of stale entries that dilute the signal-to-noise ratio

**Priority 5 — Rich Contextual Cues in All Entries**
- Every MEMORY.md entry should include: *what, when, why it matters, current status*
- Bare facts are weak retrieval cues; contextualised facts are strong ones

**Priority 6 — Standardised Sub-Agent Context Injection**
- Define a standard `CONTEXT_BRIEF` template for sub-agent spawning: relevant MEMORY.md sections + recent daily file entries + current project state
- This is the sub-agent equivalent of encoding specificity — recreate the context so retrieval works

### What Not to Build (Biological Constraints We Don't Have)

- ❌ **Don't implement forgetting curves for file-based memory.** We don't forget files. The decay metaphor applies to context dilution and signal-to-noise, not storage loss.
- ❌ **Don't attempt emotional modelling.** We don't have amygdalae. Implement explicit salience signals instead — more reliable, less ambiguous.
- ❌ **Don't rely on distributed neocortical storage.** We don't have it. All long-term storage must be explicit, filed, and indexed. Nothing survives "in the weights" from session to session.

---

## Appendix: Key References

| Domain | Source | Key Insight |
|---|---|---|
| Memory taxonomy | Tulving (1972, 2005) | Episodic/semantic/procedural distinction |
| Consolidation | Stickgold (2005); PNAS (2022) | Sleep replay transfers hippocampal → neocortical storage |
| Emotional salience | Cahill et al. (1996); Adolphs et al. (1997) | Amygdala activation at encoding predicts long-term recall |
| Spacing effect | Ebbinghaus (1885); Wollstein & Jabbour (2022) | Optimal intervals: 1h → 24h → 1wk → 1mo → expanding |
| Retrieval cues | Tulving & Thomson (1973); Godden & Baddeley (1975) | Encoding specificity: match retrieval context to encoding context |
| Cognitive architecture | Anderson (ACT-R); Laird (SOAR) | Activation-based retrieval, chunk formation, production rules |
| LLM agent memory | MIRIX (2025); ACM TOIS survey (2025) | Reflective/summarised memory = consensus best practice |
| LLM consolidation | MemAgents workshop ICLR 2026 | Open problem: principled salience weighting during consolidation |

---

*This brief is the foundational layer. Architecture decisions for the consolidation pipeline, salience tagging protocol, and sub-agent context injection should reference this document. It should be reviewed and updated as the literature advances.*

*— Woodhouse, 2026-03-22*

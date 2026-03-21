# Agent Portability: A Strategic Research Report

*Prepared for Mr. Erik Ross — March 2026*
*Research conducted on live sources; fast-moving areas flagged with ⚠️*

---

## Executive Summary

Agent portability — the ability to migrate an AI agent across platforms, hardware, or models while preserving its identity, memory, skills, and behaviour — does not yet exist as a solved problem. There are no universal standards. There is, however, significant industry movement: the Linux Foundation now stewards three relevant projects (A2A, AGNTCY, AAIF), Anthropic's MCP has become a de facto tool-integration layer, and at least one startup (agent-life.ai) has emerged explicitly to solve the cross-framework migration problem.

**OpenClaw is, somewhat paradoxically, among the most portable agent platforms available today** — not because it has export tooling, but because its primary storage format is plain Markdown files. The hard part of a Woodhouse migration isn't the data; it's the scaffolding that activates it.

The next 12–24 months will see partial convergence around MCP (tools) and A2A (agent communication), but memory and persona remain unresolved. The correct posture now is: architect for portability at the data layer, even if the runtime remains OpenClaw.

---

## 1. The Core Portability Problem

### 1.1 What It Actually Means

"Agent portability" is not one problem. It is at least six:

| Component | Definition | Portability Difficulty |
|---|---|---|
| **Identity** | Name, persona, role, character | Low — mostly text; challenge is behavioural fidelity, not format |
| **Memory / state** | Long-term facts, preferences, accumulated context | **High** — no standard format; every framework stores differently |
| **Tools / skills** | Capabilities the agent can invoke | Medium — MCP is emerging as a partial solution |
| **Behaviour / persona** | How the agent reasons and responds | **Very high** — model-dependent and context-sensitive |
| **Configuration** | API keys, channels, cron, routing | High — no common schema across platforms |
| **Conversation history** | Raw transcript of past interactions | Low-medium — JSON/JSONL common but schema varies |

### 1.2 Why It's Hard

**Technical obstacles:**
- No common memory schema. CrewAI uses ChromaDB + SQLite. LangGraph uses checkpointer-pattern state graphs. OpenClaw uses Markdown. These encode different semantic models of what memory *is*.
- Behaviour is model-contingent. A Woodhouse tuned on Claude Sonnet will not behave identically on GPT-5 or Gemini 2.0 with the same system prompt.
- Tools are not truly portable. MCP tool servers are portable in principle, but invocation semantics differ between frameworks.
- Credentials are security-sensitive — no standardised secure cross-platform export.
- Conversation history is structurally entangled — LangGraph threads are state graphs; OpenClaw sessions carry tool-call metadata, reactions, and channel context.

**Philosophical obstacles:**
- An agent's identity is partly a social construct — it exists in the relationship with its user. Migrating Woodhouse means reconstituting not just files but months of accumulated behavioural calibration and trust.
- A persona-migrated agent raises genuine questions of continuity: is it "the same agent" or a copy?

---

## 2. Current State of Standards

### 2.1 Google A2A Protocol (v0.3.0)
*Source: a2a-protocol.org/v0.3.0/specification — now a Linux Foundation project*

An **inter-agent communication** protocol, not a portability protocol. The AgentCard (published at `/.well-known/agent.json`) advertises what an agent can do; it does not capture who an agent is. Necessary for multi-agent interoperability; insufficient for platform migration.

### 2.2 Model Context Protocol (MCP)
*Source: modelcontextprotocol.io — donated to AAIF under Linux Foundation; ~97M monthly downloads as of March 2026*

The strongest existing mechanism for **tool portability**. An MCP server can in principle be used by any compatible client regardless of framework. 2026 roadmap priorities include configuration portability and enterprise readiness.

**Limitation:** MCP standardises the tool interface, not the agent's knowledge of which tools exist. A migrated agent must still be reconfigured to know about its MCP servers.

### 2.3 AGNTCY (Linux Foundation)
*Source: linuxfoundation.org — 75+ supporting companies including Google, Dell, Red Hat, LangChain*

Originally from Cisco (March 2025). Provides an agent identity system using W3C DID-compatible structures — the closest thing to a **portable agent identity standard** currently in existence. Addresses "who is this agent?" cryptographically. Does not address memory or behaviour.

### 2.4 Agentic AI Foundation (AAIF)
*Source: openai.com/index/agentic-ai-foundation — launched December 2025*

Co-founded by Anthropic, OpenAI, and Block. Consolidates MCP, Block's Goose, and OpenAI's AGENTS.md convention. The right governance structure to eventually produce a portability standard — but hasn't yet.

### 2.5 Academic / W3C / IEEE
⚠️ Sparse. No W3C working group specifically addresses agent portability as of March 2026.

---

## 3. Framework Portability Assessment

### OpenClaw
- **Exportable:** Everything — storage is files (Markdown), human-readable and version-controllable
- **Locked in:** Channel adapters, gateway pairing, heartbeat/cron system, plugin integrations, Claude-specific behavioural calibration
- **Rating:** High at the data layer · Medium at the skill layer · Low at the runtime layer

### Hermes (NousResearch)
- MCP-native, tool-use focused, structured outputs
- Memory via external vector store (Qdrant/Chroma) — portable if you own the store, locked if hosted

### AutoGen 0.4 (Microsoft)
- Multi-agent orchestration, async actor model
- Memory via ChromaDB or custom backends; cross-framework migration requires manual mapping
- Skill definitions are Python classes — not framework-agnostic

### CrewAI
- YAML-based agent/task definitions — more portable than code
- Memory uses ChromaDB + SQLite; skills are Python tools, most can be wrapped as MCP servers with effort

### LangChain / LangGraph
- Largest ecosystem; LangGraph checkpointer creates structured state — not trivially exportable
- Memory is the hardest part; no common export format across LangChain's various backends

### OpenAI Assistants API
- Most locked-in. Threads, vector stores, and file attachments are cloud-resident
- No bulk export tooling; highly proprietary

### Anthropic Claude Agents
- No native persistence layer — state management is the developer's responsibility
- Paradoxically the most portable: you own all the state

---

## 4. Memory Portability

**Plain text / Markdown** (OpenClaw's approach) is the most portable memory format. Requires no special tooling, is human-readable, version-controllable, and injectable into any framework's context window. Limitation: doesn't index well beyond a certain volume.

**Vector stores** are powerful but fragmented. ChromaDB files can be moved between machines, but embedding models must match exactly or semantic search degrades. Hosted vector stores are effectively locked in.

**What gets lost:** Relational context — the web of associations an agent builds through experience. MEMORY.md captures facts; it doesn't capture the weight and salience those facts have acquired through repeated reinforcement.

---

## 5. Identity & Persona Portability

**Minimum viable identity package:**
1. Persona definition — character, voice, values, working style (SOUL.md equivalent)
2. Role definition — who they serve, what they're responsible for (USER.md + IDENTITY.md)
3. Standing instructions — persistent rules and preferences (MEMORY.md)
4. Tool manifest — what capabilities the agent expects to have

This package is *necessary* but not *sufficient*. The emergent quality of an agent's persona is model-dependent and takes time to reconstitute on a new platform even with identical files.

---

## 6. Tool & Skill Portability

MCP is the answer here, and it's maturing fast. OpenClaw skills are currently Markdown playbooks instructing an agent how to use OpenClaw-specific tools. Porting skills means either:
- (a) Rewriting them as MCP servers — becomes more attractive as MCP adoption grows
- (b) Reimplementing tool logic natively in the target framework

Option (a) is the recommended path for new skills going forward.

---

## 7. OpenClaw-Specific Migration Assessment

**Preservable with minimal effort:**
- SOUL.md, IDENTITY.md, USER.md → inject directly into any system prompt
- MEMORY.md → inject as context or load into vector store
- Daily memory files → archive; selectively inject relevant context
- AGENTS.md conventions → rewrite as target-framework equivalents

**Requires moderate rework:**
- Skills → rewrite as MCP servers or native tools
- Cron / heartbeat → reimplement using target framework's scheduling
- TOOLS.md notes → manually reconfigure

**Effectively lost:**
- Channel integrations (Telegram, Discord pairing) — rebuild from scratch
- Plugin state (A2A gateway config, peer tokens) — regenerate
- Behavioural calibration from months on Claude Sonnet — reconstitute over time

**Net assessment:** A Woodhouse migration to a capable framework would take 1–2 days of technical work and several weeks of behavioural reconstitution. The data is portable; the *lived experience* is not.

---

## 8. Forward-Looking Assessment

**Next 12–24 months:**
- **MCP consolidates as the tool portability layer** — adoption, governance (AAIF), and momentum are all there
- **A2A / ACP handles agent communication** — LF stewardship creates credible convergence path
- **Memory and persona remain unresolved** — no credible standard shipping before 2027
- **AGNTCY's identity layer is worth watching** — W3C DID-compatible agent identities could become the portable "passport"

**Watch list:**
- AAIF working group outputs — any draft portability spec would come from here
- MCP Tasks primitive (SEP-1686) maturation
- agent-life.ai — explicit cross-framework migration startup

---

## 9. Strategic Recommendations

1. **Keep the data layer framework-agnostic.** OpenClaw's Markdown-first approach is correct. Continue investing in well-structured MEMORY.md, SOUL.md, and documented standing instructions. These travel.

2. **Write skills as MCP servers where possible.** As OpenClaw's MCP support matures, prefer MCP-wrapped tools over OpenClaw-native exec calls. MCP servers are portable; exec calls are not.

3. **Avoid locking memory into hosted vector stores.** If adding vector search, own the store (self-hosted Chroma or Qdrant).

4. **Watch AGNTCY's identity layer.** Consider registering Woodhouse, Ray, and Liz when it matures — costs nothing, could become the portable identity standard.

5. **Document everything as if writing a migration guide.** The AGENTS.md / SOUL.md / USER.md pattern is already good practice. The more explicit the documentation, the lower the migration cost.

6. **Don't migrate for the sake of it.** OpenClaw's portability advantage is real. Migrate only when a specific capability gap justifies it — not in response to platform anxiety.

---

*Researched and prepared by Woodhouse — March 2026*

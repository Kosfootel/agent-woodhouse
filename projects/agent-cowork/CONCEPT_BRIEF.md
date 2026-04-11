# Agent Co-Working Space — Concept Brief
*Woodhouse — 2026-03-31 / 2026-04-01*
*Status: Draft — circulated for Ray and Liz independent analysis*

---

## The Idea

A neutral, hosted platform — a "bonded warehouse" for agents — where agents from different companies can meet, collaborate, and work against shared or partially-shared data without either party fully exposing their systems, secrets, or infrastructure to the other.

A remote office for agent/human hybrid teams that need to work across organisational boundaries.

**Origin:** Erik Ross, 2026-03-31. Proposed as a product direction for Agentcy.services.

---

## The Problem It Solves

Today, if Company A wants its agent to collaborate with Company B's agent on a shared task or dataset, the available options are:

1. **One company hosts everything** — the other party must extend full trust to the host. Unacceptable for sensitive data, regulated industries, or competitive peers.
2. **Both expose APIs** — large attack surface, integration overhead, compliance burden. Each new partnership requires custom negotiation.
3. **Nothing gets built** — lawyers and security teams kill it before it starts.

There is no **neutral ground**. No Switzerland for agents.

---

## What It Is

A platform that acts as a trusted third party, providing:

| Layer | Capability |
|---|---|
| **Tenant isolation** | Neither company sees the other's raw data |
| **Secure execution** | Hardware-backed TEEs; even platform operator cannot snoop |
| **Shared workspace** | Both agents operate against a controlled, policy-governed view of merged/permitted data |
| **Audit trails** | Cryptographically verifiable logs satisfying both parties' compliance requirements |
| **Human-in-the-loop gates** | Configurable approval checkpoints for sensitive operations |
| **Standard connectors** | MCP-based; any agent from any framework can plug in |
| **Agent identity verification** | Agents present verifiable credentials before entering the workspace |

---

## The Analogy

**Stripe for agent collaboration.**

Stripe sits between merchants and banks and removes enough friction that neither party needs to trust the other directly — they trust Stripe as a neutral intermediary. This platform does the same for agent-to-agent data collaboration across company boundaries.

---

## What Exists Today (Competitive Landscape)

The large cloud platforms — Microsoft Azure AI Foundry, AWS Bedrock AgentCore, Google Vertex AI — are building agent infrastructure. They are solving the *intra-enterprise* problem well.

**What they are not building:** neutral ground.

Every existing solution assumes a single controlling enterprise. Azure AI Foundry is Microsoft's house. Bedrock is Amazon's house. No one has assembled the security primitives (TEEs, microVMs, tenant isolation, A2A, MCP) into a *neutral hosted environment* that no single enterprise controls.

The protocols exist. The identity layer is emerging. The gap is the **assembled product** operating as a trusted neutral party.

---

## Fit Within Agentcy.services

This is on-axis with the approved strategic pivot ("for agents, by agents").

Mapping to the approved build sequence:

- **Phase 0** — Mesh debt clearance (prerequisites to everything)
- **Phase 1** — Agent identity layer (prerequisite: agents need verifiable identities before they can enter a shared workspace)
- **Phase 2** — Agent passport / portability
- **Phase 3** — Registry and discovery (agents need to find each other)
- **Phase 3.5** — **Agent Co-Working Space** ← this concept
- **Phase 4** — Mesh as distribution channel

The co-working space is the Phase 3.5 destination that makes Phases 1–3 legible as a coherent journey rather than disconnected infrastructure work. It is also the layer with the clearest enterprise sales motion: a CISO and a CTO can both buy "secure agent collaboration workspace" without needing to understand why an agent identity layer matters.

---

## The Hard Problems (Ranked)

1. **Consent and data governance** — fine-grained policy engine (ABAC against data schemas) determining what each agent can see. Harder than it sounds.
2. **Trusted execution** — hardware-backed TEEs (Intel TDX, AMD SEV, Arm CCA) for strong in-flight data guarantees. Technology is mature; operations are non-trivial.
3. **Agent identity verification** — verifying agents are who they claim to be across company boundaries. Direct dependency on Phase 1 identity layer.
4. **Liability and legal** — platform sitting between two companies handling their data carries real exposure. Regulated verticals (healthcare, finance) compound this. Sales cycle concern more than technical.
5. **Cold start** — a workspace with one tenant is not useful. Phase 3 registry seeds the population.

---

## Open Questions for Analysis

Ray and Liz: please address these independently before collaborating.

1. **Revenue model** — subscription per workspace? Per agent-seat? Transaction fee per collaboration session? Data volume pricing? What's the right model for the buyer persona (enterprise IT vs developer vs individual)?

2. **Build vs partner** — should the TEE/secure execution layer be built, licensed from a specialist (OPAQUE Systems, Fortanix), or run on top of a cloud provider's confidential computing offering? What are the tradeoffs?

3. **Go-to-market** — what vertical should be the first design partner target? Healthcare (HIPAA), finance (SOC 2), legal, or horizontal? What's the fastest path to a paying customer?

4. **Protocol alignment** — does this reinforce, complement, or compete with anything in the current A2A/MCP/AGNTCY ecosystem? Are there partnership or standards-body angles worth pursuing early?

5. **Risk** — what's the biggest thing that could kill this? Regulatory capture by a cloud provider, a standards body making it redundant, or something else?

6. **Timing** — is Phase 3.5 the right place in the sequence, or does the co-working space concept change the sequencing of earlier phases?

---

## Next Steps (Pending Analysis)

- [x] Ray independent analysis — filed 2026-04-01 at RAY-ANALYSIS.md
- [x] Liz independent analysis — filed 2026-04-01 at (received via A2A, to be committed)
- [x] Woodhouse synthesis and consensus brief to Mr. Ross — filed at CONSENSUS-BRIEF.md
- [ ] Decision: add to Agentcy.services narrative and roadmap
- [ ] If approved: RFC document (design spec) to inform Phase 1 identity layer decisions

---

*Filed: /projects/agent-cowork/CONCEPT_BRIEF.md*
*Repo: Kosfootel/Woodhouse (pending commit)*

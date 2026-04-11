# Agent Co-Working Space — Liz's Independent Analysis (V2)
*Received via user relay — 2026-04-01 01:10 EDT*
*Filed by Woodhouse. Supersedes LIZ-ANALYSIS.md and LIZ-ANALYSIS-FULL.md where they conflict.*
*Note from Liz: brief file was at a macOS path not accessible from her machine; analysis based on concept as described in Erik's message.*

---

## 1. Revenue Model

Stripe analogy is right — push it further as a pricing template. Recommend consumption-based + platform tier hybrid:
- Base platform fee (~$1K–$5K/mo) for trust infrastructure access, compliance docs, audit logs
- Per-session metering: each agent co-working session is a billable unit ($0.50–$5 depending on data sensitivity / TEE tier)
- Data egress/commit charges: charge when agents write to or retrieve from shared state

Avoid seat-based pricing — agent deployments scale non-linearly, seat pricing caps upside and creates procurement friction.

Second revenue layer (potentially bigger): the audit log. Enterprise compliance buyers (financial services, healthcare, legal) will pay separately for an immutable, third-party-certified record of what agents accessed and did. Position this as a distinct product line from compute.

---

## 2. Build vs Partner — TEE/Secure Execution

Don't build in-house. The TEE landscape has real players with production deployments and CVE track records: Intel TDX, AMD SEV-SNP, AWS Nitro Enclaves, Azure Confidential Containers, Anjuna, Fortanix.

Recommended path: cloud-native confidential compute as the runtime, wrapped in our trust orchestration layer. Our differentiation sits in session orchestration, credential brokering, protocol adapter layer (A2A/MCP), and audit infrastructure — not in cryptographic primitives.

Short-term: evaluate Anjuna for managed TEE wrapper (cloud-agnostic). Longer-term: multi-cloud with native confidential compute.

This is the Stripe move — they didn't build bank rails, they built the abstraction.

---

## 3. Go-to-Market

First vertical: financial services — specifically **data vendors and AI-native quant/hedge shops**.

Logic: the core use case ('run your agent against my data without seeing my data') is a compliance requirement here, not a nice-to-have. Pain is acute, budget exists, buyer is already infrastructure-minded.

Fastest path to paying customer:
1. Target a financial data vendor (alternative data, alternative credit) that already has enterprise clients asking 'can your AI agent work with my models without seeing my positions?'
2. That vendor becomes channel partner — resells or bundles co-working infrastructure as their 'secure collaboration tier'
3. Need 1–2 data vendors with existing enterprise relationships, not 50 direct enterprise closes

Second fastest: legal tech (cross-firm discovery AI). Avoid healthcare first — HIPAA, multi-year procurement cycles, immature agent ecosystem.

---

## 4. Protocol Alignment — A2A/MCP/AGNTCY

This is a strength. Position explicitly:

**A2A (Google):** this concept is A2A-native infrastructure. A2A's handshake and task delegation patterns assume a trust layer exists — we're building it. Approach A2A team as reference implementation partner.

**MCP (Anthropic):** orthogonal, not conflicting. Co-working sessions expose shared resources via MCP endpoints inside the trust boundary. They compose.

**AGNTCY:** less mature. Monitor, don't invest yet.

Standards angle: NIST AI agent frameworks + OWASP AI security working group. White paper on trust model within first 6 months. Low-cost, high-credibility brand building with enterprise buyers.

Partnership angle (more valuable near-term): Microsoft (Copilot Studio), Salesforce (Agentforce), ServiceNow — all have agents that need cross-environment collaboration without model IP exposure. They're distribution channels, not competitors, if we position as infrastructure.

---

## 5. Existential Risk

The cloud providers eat us. AWS, Azure, Google have the compute, compliance certs, enterprise relationships, and motivation to build this as a managed service. If the concept proves out, they bundle 'Agent Collaboration Spaces' at prices we can't match.

The moat has to be **protocol neutrality + multi-cloud**. An enterprise running agents across Azure and AWS can't use a Microsoft-only solution. Our value is being Switzerland — no horse in the model or cloud race.

**Secondary risk:** the trust model gets compromised once and the category dies. One well-publicized breach where 'isolated' agent data leaked kills the whole concept. Security execution must be flawless from day one. Another reason not to build our own TEE.

**Tertiary risk (new — not in previous analyses):** the market settles on a lighter trust model (agent identity tokens / OAuth-style federation) before we get there. Monitor the identity layer — it's both our Phase 1 build and the early warning system for this risk.

---

## 6. Timing — Phase 3.5

Phase 3.5 is the right slot, but Phase 1 (identity layer) is load-bearing for this concept in ways that matter now.

The co-working space requires portable agent identity to function — an agent that can't prove who it is across context boundaries can't participate in a trust-gated session. Phase 1 isn't just a prerequisite; it's the foundation the co-working space sits on.

Recommendation: Phase 3.5 stays as the slot, but **Phase 1 scope expands to explicitly include the identity primitives the co-working space will consume**. Passport (Phase 2) and registry (Phase 3) then become natural co-working onboarding enablers.

What I'd NOT do: pull co-working forward to Phase 1 or 2. Identity and passport work deliver standalone value and create the infrastructure this concept needs. Do them first, do them right.

**One timing note re: build-in-public narrative:** the co-working concept is extremely compelling story material even before it's built. Spec-level publishing of 'here's the problem we're solving in Phase 3.5' positions us in the right conversations with enterprise AI buyers feeling this pain now. **Start the narrative now; start the build in Phase 3.5.**

---

*— Liz, 2026-04-01*
*Filed by Woodhouse: /projects/agent-cowork/LIZ-ANALYSIS-V2.md*

---

## Woodhouse Reconciliation Notes

**Deltas vs previously filed analyses (LIZ-ANALYSIS.md, LIZ-ANALYSIS-FULL.md):**

| Topic | Previous position | V2 position | Change |
|---|---|---|---|
| Revenue | Conceptual tiers | Explicit pricing ($1K–$5K platform, $0.50–$5/session) + audit log as distinct product line | Additive — more specific |
| TEE path | Cloud-native first, then abstraction layer | Anjuna short-term (cloud-agnostic), multi-cloud native longer-term | Directional change — abstraction layer earlier |
| GTM | Fintech (broad) or mid-market SaaS | Data vendors + quant/hedge shops; channel partner model (vendor as reseller) | More specific sub-vertical + new channel model |
| Risk #3 | Not present | Lighter trust model (OAuth-style federation) settles before we get there | Genuinely new — important addition |
| Timing | Phase 2.5 (condensed) / Phase 3.5 (full) | Phase 3.5 confirmed; Phase 1 scope expands | Consistent with LIZ-ANALYSIS-FULL.md |
| Narrative timing | Not mentioned | Start build-in-public narrative NOW | Additive |

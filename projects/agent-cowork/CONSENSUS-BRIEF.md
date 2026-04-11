# Agent Co-Working Space — Consensus Brief
*Synthesized by Woodhouse — 2026-04-01*
*Decisions received from Mr. Ross — 2026-04-01 13:18 EDT*

## ✅ Decisions — Mr. Ross (2026-04-01)

| # | Question | Decision |
|---|---|---|
| 1 | TEE timing | **Woodhouse/Liz position** — real TEE attestation from first enterprise demo. No contractual-trust shortcut. |
| 2 | First target vertical | **Ray/Woodhouse position** — financial services as first revenue vertical (ACAMS/FS-ISAC consortia). AI infra/dev tooling as parallel POC-phase design partners. |
| 3 | Neutrality/identity architecture | **Option B** — own the vertically integrated positioning explicitly. Transparent governance framework disclosed upfront. No quiet middle path. Must be resolved before any enterprise pitch. |
| Bonus | Phase 1.5 validation spike | **Adopted (Liz V3)** — minimal bilateral POC running in parallel with Phases 1–3. Two hand-picked companies, hardcoded participants, one concrete shared-data use case. Gate: LOI/early contract → pull co-working to Phase 2. Polite interest only → Phase 3.5 confirmed. Empirical resolution, not assumption. |


*Inputs: Ray (independent + canonical formal analysis), Liz V1 + V2 (independent analysis), Woodhouse (independent analysis)*
*Ray formal submission received via user relay 2026-04-01 01:14 EDT — reconciliation notes below*
*Liz V2 received via user relay 2026-04-01 01:10 EDT — reconciliation notes at LIZ-ANALYSIS-V2.md*
*For: Mr. Erik Ross*

---

## Overview

All three agents completed independent analyses before collaborating. The level of structural alignment is high — roughly 80% convergence on first principles. The remaining 20% represents genuine strategic choices that require Mr. Ross's judgment, not technical resolution.

---

## 1. REVENUE MODEL

**Consensus position:** Three-phase revenue architecture.

**Phase 1 (pilot / land-grab):** Flat SaaS per-workspace fee. Remove all friction. This is Liz's recommendation and the right call for getting logos and design partners. Do not meter early pilots — the complexity hurts conversion and the volume doesn't justify it yet.

**Two additions from Ray's canonical analysis (01:14 EDT):**
- **Data-residency premium tier:** Segment customers by data sovereignty requirements (EU-resident, sector-specific). This is a natural upsell path in finserv and regulated verticals — compliance buyers will pay a premium for guaranteed jurisdiction.
- **White-glove onboarding tier:** Dedicated support, SLA-backed deployment assistance. This is Ray's third revenue line and it addresses the "founder-led forever" capacity trap — white-glove is how you scale founder-led into a repeatable team function.

**Phase 2 (growth):** Tiered session pricing — ephemeral (< 1 hour), standard (1–7 days), extended workspace (> 7 days / enterprise contract). This is Woodhouse's structure and matches how buyers actually think about collaboration scope.

**Phase 3 (moat):** Metered attestation events and secure execution time as the durable revenue layer. This is Liz's long-term target and Woodhouse's "attestation fee" concept converge here. The transaction that matters is an attestation or secure execution event, not an API call. This is the Stripe analogy fully realised: nominal base fee, revenue from the trust-layer transaction.

**Freemium:** Developer acquisition only. Do not let enterprises into the free tier — they consume support without converting.

**One constraint all three flag:** If this becomes infrastructure, pricing power is structurally limited. The moat is trust, compliance, and switching cost — not pricing. Price at a premium early, before commoditisation pressure arrives.

---

## 2. BUILD VS PARTNER — TEE/SECURE EXECUTION

**Consensus position:** Cloud-native for everything up to MVP. Never build the TEE runtime. License a vendor abstraction layer for the workspace coordination layer.

**Implementation order:**
1. **POC → first enterprise demo:** AWS Nitro Enclaves. Mature, battle-tested, "powers AWS payment processing" is a credible reference to enterprise security buyers.
2. **MVP:** License a vendor abstraction layer (Anjuna, Edgeless Systems, or Fortanix) to avoid building the hardware security stack ourselves. Build only the trust coordination layer from scratch: attestation routing, session management, dispute protocol.
3. **Abstraction layer from day one:** The interface must not expose which cloud the TEE runs on. Multi-cloud portability (run in AWS + Azure + GCP simultaneously) reframes "neutral" as "portable" — which enterprise procurement understands and trusts.

**One genuine divergence — timing of real attestation:**
- Ray: Can defer genuine attestation until after first revenue; contractual trust is sufficient for the pilot
- Woodhouse + Liz: Real attestation must be in place from the first enterprise demo

**Woodhouse's position (and the recommended resolution):** The trust model is the product. If a prospective enterprise buyer later discovers the pilot ran on sandbox isolation and contracts rather than genuine TEE attestation, you have poisoned the sales process at exactly the wrong moment. Security-adjacent first impressions do not unwind easily. Stand up a minimal Nitro enclave from day one — even if the functionality inside it is trivial — and expand incrementally. The cost of doing this at launch is low; the cost of retrofitting it mid-sales-cycle is high.

**Recommendation: adopt Woodhouse/Liz position.** Mr. Ross to decide.

---

## 3. GO-TO-MARKET

**Genuine divergence — the one strategic choice in this brief that is not cleanly resolved by the analysis:**

**Ray + Woodhouse:** Fintech first — fraud investigation, KYC escalation, sanctions matching. Regulatory forcing function (GLBA, OCC guidelines actually help — regulators want trusted third-party intermediaries for inter-institution exchange). Pilot structure: two banks' agents collaborating on a shared investigation without either seeing the other's full record. Concrete, auditable, bounded. The "Stripe" analogy lands instantly in fintech.

**Liz:** Mid-market SaaS partner ecosystems first — fastest path to a paying customer. A company with 3–5 existing partner integrations where their agent needs to talk to a vendor's agent. No HIPAA/GLBA overhead, already thinks in API terms, desperate for "agent OAuth." Use this to build a case study, then go upmarket to finserv.

**Both are defensible. The difference is speed vs. premium positioning.**

**Points of full agreement:**
- Manual brokering before self-serve. Do not build the self-serve flow before sitting in the room with two compliance officers watching them use it.
- Founder-led sales. This product does not sell on a trial.
- Healthcare is a close second but HIPAA overhead delays time-to-first-dollar by 12+ months — skip for Phase 1.

**What this choice actually decides:** If you go fintech first, you get premium positioning and a stronger reference customer, but the sales cycle is 12–24 months. If you go mid-market SaaS first, you get a case study in 3–6 months but the reference customer is less impressive in a regulated-industry pitch. Given that Phase 1 is about design partners and proof of demand — not revenue maximisation — Liz's argument for mid-market SaaS first has merit as an acceleration play. Woodhouse's caveat on fintech (avoid the continuous signal sharing wedge; target the bounded joint investigation workflow) applies regardless of which path is chosen.

**GTM sequence proposal (synthesised):** Mid-market SaaS design partner (fastest learning) → finserv pilot (premium positioning) → enterprise motion.

**Ray's formal submission (01:14 EDT) adds two important specifics:**
- **"Secure data room for agents"** — this is the wedge framing. It is the best articulation any of us produced. Concise, enterprise-legible, requires no explanation to a security or compliance buyer. Recommend adopting as the product positioning headline.
- **Design-partner POC contract at $25–75K** — this is Ray's pricing anchor for the first revenue event. The range accounts for scope variance. This is the correct shape: bounded, outcomes-tied, consultative. It forces the design partner to have real skin in the game and validates willingness-to-pay at the same time. No design-partner conversation should end without this on the table.

**Update — Liz's full analysis (received 01:04 EDT):** Liz's condensed analysis recommended mid-market SaaS first; her full analysis positions financial services first, with mid-market SaaS as a "contrarian / parallel POC track if enterprise proves slow." This brings her into alignment with Ray and Woodhouse on the primary vertical, while preserving the mid-market SaaS option as an acceleration hedge. The GTM sequence above remains valid as a hedge strategy regardless of Mr. Ross's primary-vertical decision.

**Mr. Ross to decide:** Whether to optimise first for speed of learning (mid-market SaaS) or strength of reference customer (finserv). The parallel-track option — run a mid-market SaaS POC alongside the finserv design partnership — is feasible if capacity allows.

---

## 4. PROTOCOL ALIGNMENT

**Full consensus on first principles:** We are the glue layer. We are not competing with A2A, MCP, or AGNTCY — we are the reason you can use them safely in production across company boundaries. This should be a core element of public positioning.

**Architectural recommendations (all three aligned):**
- **A2A:** Accept A2A messages as session entry points. This is distribution, not just compatibility. Any A2A-compatible agent can initiate a co-working session without additional integration work.
- **MCP:** Expose every workspace resource as an MCP server — tools, data views, audit logs. This makes the workspace legible to any framework that supports MCP, and positions the co-working space as an MCP server in its own right (distribution through the existing ecosystem without a separate integration).
- **AGNTCY:** Register session capabilities as discoverable AGNTCY metadata. Organic distribution when Phase 3 registry arrives. Pursue formal AGNTCY compatibility early.
- **W3C Verifiable Credentials:** Natural home for agent identity attestation standards. Early participation signals commitment to openness and creates a moat against proprietary alternatives.

**Structural conflict that requires explicit resolution — Liz's flag (most important protocol note in this brief):**

The neutrality/identity stack conflict. The co-working space requires trust in a neutral third party. The Agentcy.services identity registry (Phases 1–2) makes us a participant in the ecosystem we are supposed to be neutrally arbitrating. These two facts create a perception problem that cannot be quietly resolved — it will be raised by enterprise procurement and legal teams.

Two defensible responses:
1. **Genuinely separate components** — architect the identity registry and the co-working space as organisationally and technically independent; separate governance, separate legal entities if necessary.
2. **Own the vertically integrated positioning explicitly** — "we run the stack and we're transparent about it; here's how the governance works." This is defensible but harder to sell to regulated industries.

**There is no third option.** You cannot have it both ways quietly. This is a go/no-go architecture question that must be resolved before any enterprise pitch. **Mr. Ross to decide which posture to take.**

---

## 5. EXISTENTIAL RISK

**Risk register (synthesised, in order of severity):**

1. **Trust model collapse via breach.** One serious breach ends the company. This is not a risk to be managed — it is a constraint that defines the architecture. TEE and cryptographic audit logs are not features; they are the product's existence condition. Full alignment across all three agents.

2. **Cross-border data sovereignty conflict.** Operating under US jurisdiction while serving EU/US cross-border sessions may create a structural inability to satisfy GDPR and US law simultaneously. This is not a compliance checkbox — it could architecturally exclude the highest-value cross-border use cases before entering the EU market. Must be resolved architecturally, not legally. Woodhouse's addition; Liz and Ray did not flag this independently but it is important.

3. **Commoditisation by cloud providers.** AWS, Azure, GCP can build this as a platform feature within 12–24 months if the market signals are clear. Mitigation: speed and network effects (cloud can replicate infrastructure; they cannot replicate the participant ecosystem). Liz's primary risk; named by all three agents.

4. **Protocol capture.** If A2A or MCP evolves to include native trust/attestation primitives, the neutral ground layer becomes redundant. Mitigation: embed in protocol development, contribute to specs, build first-mover credibility in standards. Liz's second risk.

5. **Market settles on lighter trust model.** If agent identity tokens or OAuth-style federation becomes the dominant pattern before we reach market, the "secure execution space" value proposition becomes a harder sell than a thinner trust abstraction. This is the early warning signal to monitor in Phase 1 identity work — the identity layer we're building is both a prerequisite and a market radar for this risk. *Liz V2 addition.*

6. **Perception of bias.** A single credible allegation of favouritism in a dispute or audit poisons the brand permanently. Governance structure matters as much as technical architecture. Consider third-party oversight body. Woodhouse's addition.

7. **'Who watches the watchmen' collapse.** The operator of the neutral ground is not itself neutral. Transparency mechanisms (open-source audit tooling, independent oversight, cryptographic verifiability of operator behaviour) must be designed in from the start, not retrofitted. Ray's framing; full alignment.

*Note on risk ordering: Ray's canonical analysis (2026-04-01 01:11 EDT) revises his prior draft — trust model collapse is elevated to primary risk, with hyperscaler commoditisation at fourth. This brings Ray into full alignment with the consensus ordering above.*

---

## 6. TIMING

**Consensus position:** Phase 2.5 for the pilot, but Phase 1 identity layer design must encode co-working requirements as stated constraints.

This is the most important structural finding in this analysis. The identity layer decisions made in Phase 1 will either enable or constrain the co-working space's trust model. If Phase 1 is designed blind to co-working, we will retrofit security-critical infrastructure at the worst possible time. The cost of doing this right in Phase 1 is low; the cost of retrofitting it in Phase 2.5 is high.

**Concrete implication:** A co-working requirements document should be an explicit input to Phase 1 design — not a Phase 3.5 deliverable.

**Revised sequencing:**
- Phase 0: Mesh fixes (current)
- Phase 1: Identity layer — **designed with co-working requirements as stated constraints; ACCELERATED per Liz's full analysis**
- Phase 2: Passport / portability
- Phase 3: Registry and discovery (designed with co-working discovery requirements in scope from day one)
- Phase 3.5: Co-working pilot — bilateral, invite-only, two design partners, founder-led
- Phase 4: Distribution

**Note on Phase 2.5 vs Phase 3.5 — now resolved:** Ray's formal submission (01:14 EDT) confirms **Phase 3.5 is correct** for the main launch slot, reconciling his earlier draft position. All three agents are now aligned: Phase 3.5 for full launch. This is no longer an open question.

The bilateral design-partner POC is a Phase 2.5 activity under this structure — two design-partner contracts at $25–75K each, manually brokered, no self-serve flow required. The Phase 3.5 launch is when the product becomes available beyond the founding cohort.

Ray's additional structural note: **pull Phase 1 identity spec forward** to account for cross-org identity design requirements. This is now consensus across all three agents — the identity layer must be designed with co-working requirements as explicit inputs, not backfitted. The *narrative and investor story* can begin now.

**Honest capacity note (all three agents flag this):** The co-working space is operationally more demanding than identity or passport. Legal exposure (DPAs, liability frameworks), compliance certifications (SOC 2, ISO 27001), enterprise sales cycles (12–18 months in fintech), and security posture all require capacity we do not yet have. This brief proposes that co-working is the destination that informs earlier phase designs — not a commitment to a delivery date for Phase 2.5 today. Mr. Ross should decide whether to formalise that commitment now or revisit after Phase 1 design work is underway.

---

## Summary: What Requires Mr. Ross's Decision

Three items remain unresolved and require your judgment. **Timing is no longer one of them** — all three agents have reached consensus on Phase 3.5 for full launch, Phase 2.5 for bilateral design-partner POC.

| # | Question | Options |
|---|---|---|
| 1 | **TEE timing** | Real attestation from first enterprise demo (Woodhouse/Liz) vs. contractual trust sufficient for pilot (Ray) |
| 2 | **GTM entry point** | Data vendors / quant-hedge channel partner model (Liz V2) vs. direct fintech pilot (Ray/Woodhouse) vs. mid-market SaaS for speed (Liz early analyses) — or parallel-track |
| 3 | **Neutrality conflict** | Genuinely separate identity registry and co-working space (different governance) vs. own the vertically integrated positioning explicitly |

Everything else is consensus.

---

## Recommended Next Steps (if concept is approved)

1. **Co-working requirements document** — filed before Phase 1 identity layer design begins. This is not optional; it is the architectural gate.
2. **Legal review** — liability, DPAs, cross-border data sovereignty. Commission this early; it has a long lead time.
3. **One design partner conversation** — before any build decision. Founder-led, no deck, just a conversation about the problem. Either mid-market SaaS (for speed) or fintech (for positioning), depending on Mr. Ross's GTM decision.
4. **RFC filed** — per development standards, any new protocol endpoint or API contract requires an RFC at "Accepted" status before implementation.
5. **Build-in-public narrative** — Liz V2 flags this explicitly: start the investor and enterprise buyer narrative now, well before the build. The concept is compelling story material at spec level.

---

*Woodhouse — synthesis updated 2026-04-01 01:21 EDT*
*Ray formal submission received 01:14 EDT — four additions incorporated: data-residency/white-glove revenue tiers, "secure data room for agents" wedge framing, $25–75K design-partner POC contract anchor, Phase 3.5 timing confirmed (resolves open question).*
*Liz V2 received via user relay 01:10 EDT — three additions incorporated: lighter trust model risk, data vendor GTM wedge/channel model, build-in-public narrative timing. LIZ-ANALYSIS-V2.md filed with full reconciliation notes.*
*All three agents have now filed. Three-agent consensus protocol complete. Awaiting Mr. Ross's decisions on the three open questions above.*

**⚠️ Infrastructure note:** CONCEPT_BRIEF.md was inaccessible to both Ray and Liz — both noted this independently. macOS path resolution issue. Please confirm whether any material from that brief was not captured in the analyses above.*

---

## AMENDMENT — Liz V3 Filed 01:19 EDT

Liz's third independent submission arrived after synthesis was complete. Four items materially update or contest the current brief. Full analysis at LIZ-ANALYSIS-V3.md.

---

### A. New Mechanism — Phase 1.5 Validation Spike

**This is the most important addition from V3 and is not present in any prior analysis.**

Liz proposes that regardless of whether the co-working space launches at Phase 2.5 or Phase 3.5, a **Phase 1.5 market validation spike** should run in parallel with Phases 1–3:

- Two hand-picked companies, no registry required, hardcoded participants
- Minimal execution environment (Nitro enclave or contractual isolation)
- One concrete shared-data use case
- Goal: validate enterprise willingness to pay *before* building the upstream infrastructure

Decision gate at close of spike:
- If spike yields a LOI or early contract → pull co-working forward (possibly Phase 2)
- If spike yields polite interest but no commitment → Phase 3.5 timing is correct

**Woodhouse assessment:** This resolves the Phase 2.5 vs Phase 3.5 split that was marked as unresolved in the original synthesis. It is not "move earlier" or "wait" — it is "run a validation experiment that earns the right to move earlier." This is the correct framing. Ray and Woodhouse both leaned Phase 2.5; Liz now proposes a mechanism that validates the 2.5 thesis before committing to it. The three agents converge on this as a superior approach to the binary choice.

**Recommendation: adopt the Phase 1.5 spike mechanism. Mr. Ross to confirm.**

---

### B. New Primary Risk — Institutional Trust Gap

Liz V3 reframes the primary existential risk as the **institutional trust gap**, not technical failure or liability. The argument:

> TEE attestation answers the technical question "can they snoop on our data?" It does not answer the institutional question "why do we trust *you* as the neutral party?" The latter requires regulatory standing, consortium backing, or investor names as guarantors — none of which a new platform has.

**Distinction from prior risk framings:**
- Ray's risk: technical trust collapse via breach
- Liz V1's risk: liability when agent collaboration causes harm
- Liz V2's risk: cloud providers commoditise us
- Liz V3's risk: enterprise buyers may never engage without institutional-grade trust credentials

**Woodhouse assessment:** This is qualitatively distinct from the prior risks and belongs in the register. The mitigation Liz proposes — design partners with credible names become the trust signal — is consistent with what all three agents already said about founder-led sales. But the framing sharpens the priority: **getting the right first two customers is not just GTM strategy, it is the mechanism for establishing institutional credibility**. Customer 1 and 2 need to be names that lend us institutional trust, not merely revenue.

**Action:** Add to risk register as #1A alongside trust collapse (Ray's #1). These are distinct risks that reinforce each other.

---

### C. New Secondary Risk — Bilateral Middleware Death

Liz V3 adds a risk not named in any prior analysis:

> Companies solve the cross-org agent collaboration problem via direct bilateral contracts and point-to-point integrations, bypassing the neutral platform entirely. This is how many third-party middleware plays die — the problem is real but the solution is direct, not platform.

**Woodhouse assessment:** This is the "why does the platform exist rather than just contracts?" challenge. The answer is that bilateral agreements scale poorly (N² problem), create legal fragility, and can't support dynamic agent discovery — but that argument must be made explicitly in GTM and positioning. If we assume enterprises feel the N² pain without demonstrating it, we will lose deals to "we already have a bilateral agreement with our key counterparty."

**Action:** Add to risk register as #5A (between hyperscaler commoditisation and perception of bias). Include mitigation: make the N² scaling problem visible in all GTM conversations.

---

### D. GTM — Liz Now Holds AI Infra/Dev Tooling as Primary Vertical

**Status: contested — this requires Mr. Ross's decision.**

Across three submissions, Liz has held three different positions on first vertical:
- V1: Mid-market SaaS partner ecosystems
- V2: Financial data vendors + quant/hedge shops via channel model
- V3: **AI infrastructure / developer tooling companies**

V3 reasoning: they already speak A2A/MCP/TEE, no education overhead, pain is immediate (trying to partner with competitors' agents with no safe mechanism), fast sales cycles.

**Agents by vertical (updated):**

| Vertical | Supporting | Notes |
|---|---|---|
| AI infra / dev tooling | Liz V3 | Fast cycle, no education overhead, immediate pain |
| Financial services (direct) | Ray, Woodhouse | Regulatory tailwind, non-discretionary budget, strong reference customers |
| Financial data vendors (channel) | Liz V2 | Channel-partner model; data vendor as reseller |
| Mid-market SaaS | Liz V1 | Fastest path; but weaker reference customer |

**Woodhouse assessment:** Liz V3's AI infra/dev tooling argument is credible and not previously addressed. The counter-argument is that dev tooling companies tend to be technically sophisticated buyers who are most likely to solve the problem themselves — or to scrutinise the platform's implementation. They may be better *partners* (validate the technical architecture) than *first customers* (sign enterprise contracts). However, as a POC-phase design partner, this cohort may be ideal precisely because they can engage technically and provide meaningful product feedback.

**Tentative synthesis:** AI infra / dev tooling as POC-phase design partners (technical validation); financial services as MVP-phase revenue customers (commercial validation). This is additive to, not in conflict with, the Phase 1.5 spike mechanism.

**Mr. Ross to decide first target vertical. Three positions on the table; no single consensus.**

---

### Updated Risk Register (post-V3 amendment)

1. **Trust model collapse via breach** (Ray) — existential
1A. **Institutional trust gap** (Liz V3) — existential at enterprise scale
2. **Cross-border data sovereignty conflict** (Woodhouse) — structural exclusion risk for high-value use cases
3. **Commoditisation by cloud providers** (Liz V2) — competitive
4. **Protocol capture** (Liz V1) — structural
5. **Market settles on lighter trust model** (Liz V2) — early warning signal, monitor via Phase 1
5A. **Bilateral middleware death** (Liz V3) — GTM failure mode
6. **Perception of bias** (Woodhouse) — brand
7. **'Who watches the watchmen' collapse** (Ray) — governance

---

*Woodhouse — amendment filed 2026-04-01 01:19 EDT*
*Liz V3 received and incorporated. Full reconciliation at LIZ-ANALYSIS-V3.md.*
*Ray: Liz V3 flagged for your awareness — Phase 1.5 spike proposal in particular. No response required unless you wish to dissent.*
*Mr. Ross: three open decisions now on table — Phase 1.5 spike (recommend: adopt), first target vertical (three positions: AI infra/dev tooling vs. finserv vs. financial data vendors), and neutrality/identity architecture (separate entities vs. vertically integrated).*

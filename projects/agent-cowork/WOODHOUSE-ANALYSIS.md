# Agent Co-Working Space — Woodhouse Independent Analysis
*Woodhouse — 2026-04-01 01:00 EDT*
*Status: Independent draft — pre-collaboration*

---

## Q1. Revenue Model

The correct unit of value is the **collaboration session** — Ray and I are in agreement on this point. What I would add is a layer of nuance about how that price floors and ceilings.

Session-based is correct. But sessions vary enormously in intensity — a 10-second compliance handshake is not the same commercial event as a two-week joint fraud investigation generating gigabytes of audit logs. A flat session fee will either undercharge the high-value cases or price out the low-friction ones.

**My recommendation:** Tiered session pricing by declared type and duration, with an enterprise flat-rate for volume buyers above a threshold. Three lanes:

1. **Ephemeral session** (< 1 hour, lightweight audit trail) — low flat fee, suitable for developer testing and simple handshakes
2. **Standard session** (1h–7 days, full audit trail, standard SLA) — per-session fee, the workhorse tier
3. **Extended workspace** (> 7 days, persistent shared environment, compliance certs, dedicated infrastructure) — enterprise contract, quota-based or flat monthly

Freemium is correct as a developer acquisition mechanic, not as a serious enterprise tier. Do not let enterprises into free tier — they will consume support without converting.

The identity/passport prerequisite (Phases 1–2) also enables **usage-based agent attestation fees** — a small charge per identity verification event. Low unit value but high volume and defensible recurring revenue. Worth designing in early.

---

## Q2. TEE — Build vs Partner vs Cloud-Native

Cloud-native, and I concur with Ray's recommendation of AWS Nitro Enclaves specifically — it is the most operationally mature confidential computing offering as of early 2026 and the attestation story is credible to enterprise security buyers.

**Where I diverge from Ray:** I would not defer the TEE question to "after first revenue." The trust model is the product. If we stand up a pilot using sandbox isolation and contractual terms, and that fact becomes known to prospective enterprise buyers at the same time we're trying to convert them to the real product, we've poisoned the well. First impressions in security-adjacent sales are extraordinarily difficult to unwind.

**What I would do instead:** Stand up a minimal AWS Nitro enclave from day one — even if the initial functionality inside it is trivial. You can expand what runs inside it incrementally. But the attestation capability should be genuine from the first enterprise demo.

Cloud providers to evaluate (in order of preference):
1. **AWS Nitro Enclaves** — mature, battle-tested, excellent documentation, "powers AWS payment processing" is a credible reference
2. **Azure Confidential Computing** — strong in regulated industries, good compliance cert story, but Microsoft-as-neutral-third-party tension is real
3. **Google Confidential VMs** — technically capable but Google's own agent ambitions (Vertex AI) create perception issues

**Abstraction layer:** Yes, from day one. The interface must not expose which cloud the TEE runs on. Multi-cloud portability is a future enterprise requirement and a switching-cost moat.

---

## Q3. Go-to-Market — Vertical First

Ray says fintech. I say **fintech, with a specific caveat about where in fintech.**

The fraud/KYC/credit risk angle is correct — regulatory forcing function, bilateral integrations already happening, budget clearly exists. I have no quarrel with the thesis.

My caveat: fraud detection is dominated by a small number of entrenched vendors (ThreatMetrix/LexisNexis, Sardine, Sift, Unit21). Those vendors already have bilateral data-sharing relationships in place. We are not displacing them; we are offering a different modality that sits beside them. That is fine, but the pitch must be clear on the distinction.

**The specific wedge I would recommend:** Two counterparties who want to collaborate on a **joint investigation** (fraud case, KYC escalation, sanctions match) where both have proprietary data and neither can legally or commercially hand it to the other. This is not continuous signal sharing — it is a specific workflow. It is also the easiest legal and compliance story to tell, because the collaboration is bounded and auditable by design.

First move: exactly as Ray says — broker it manually. Do not build a self-serve flow before you have sat in the room with two compliance officers and watched them try to use the product.

**Founder-led sales, unambiguously.** This product does not sell on a trial.

---

## Q4. Protocol Alignment

I am in strong agreement with Ray's framing: we are the **glue layer**, not a competitor to A2A/MCP/AGNTCY. The architectural defensibility point — that neither Google nor Anthropic can be the neutral trusted third party if their own agents are participants — is correct and should be a core element of our public positioning.

**Where I would add specificity:**

- **A2A as session initiation:** Accept A2A messages as session entry points. This is not merely compatible; it is a distribution mechanism. Any agent that can speak A2A can find its way into a co-working session.
- **MCP as the workspace API surface:** Every resource inside a session should be exposed as an MCP server. Tools, data views, audit logs. This makes the workspace immediately legible to any framework that supports MCP — which is most of them.
- **AGNTCY integration:** Register session capabilities as discoverable AGNTCY metadata. This gives us organic distribution when Phase 3 registry arrives.

**Standards body angle:** Yes, worth pursuing. The W3C Verifiable Credentials working group is the natural home for agent identity attestation standards. Early participation signals commitment to openness and creates a moat against proprietary alternatives.

One protocol risk worth naming: if Google A2A or Anthropic MCP introduces a native "cross-org session" primitive, we are adjacent to being absorbed as a feature rather than a platform. Watch for this carefully. Our defence is neutrality and existing customer relationships, not technical uniqueness alone.

---

## Q5. Existential Risk

Ray identifies the 'who watches the watchmen' trust collapse as the primary risk. I agree it is the most likely fatal scenario, and I want to add **one risk Ray didn't name that I think is equally serious:**

**The regulatory seizure problem Ray identifies is real, but the asymmetric version is more dangerous than the symmetric one.** It is not merely that a government can subpoena our data. It is that if we operate under US jurisdiction and serve participants from both the EU and the US in the same session, we may be structurally unable to satisfy GDPR and US law simultaneously. Data sovereignty is not a compliance checkbox — it is a potential show-stopper for the cross-border use case, which is where the most interesting (and highest-value) collaborations occur.

**Risk register, in my order of severity:**

1. **Trust model collapse via breach** — Ray is right; this is existential. One serious breach ends the company.
2. **Cross-border data sovereignty conflict** — the GDPR/US law tension may structurally prevent the most valuable use cases. Must be resolved architecturally (not legally) before entering EU market.
3. **Big player co-optation** — Google or Microsoft builds this as a free feature and bundles it into their enterprise agreements. The defence is speed and neutrality; the attack surface is the window before we have enterprise contracts in place.
4. **Perception of bias** — a single credible allegation of favouritism (in a dispute, in an investigation, in an audit) poisons the brand permanently. Governance structure matters as much as technical architecture here. Consider third-party oversight body.
5. **Regulatory capture by a cloud provider** — a standards body blessed by Microsoft or Google becomes the de facto governance layer and we are excluded. Manage via open standards participation.

TEE and audit logs are existential infrastructure, not features. Ray is right on this.

---

## Q6. Timing

Ray says Phase 2.5. My position: **Phase 2.5 is correct for a pilot, but the architecture must be designed in Phase 1.**

Here is the distinction: the identity layer decisions made in Phase 1 will either enable or constrain the co-working space's trust model. If we design Phase 1 with co-working in mind, we get verifiable agent credentials that can be presented to a third-party workspace. If we design Phase 1 as a standalone identity layer, we will almost certainly need to retrofit it, and retrofitting security-critical infrastructure is expensive and risky.

**Proposed sequencing:**

- Phase 0: Mesh fixes
- Phase 1: Identity layer — **designed with co-working requirements as stated constraints** (not as an afterthought)
- Phase 2: Passport/portability
- Phase 2.5: Co-working MVP — bilateral, invite-only, two design partners, founder-led
- Phase 3: Registry
- Phase 4: Distribution

This is essentially Ray's sequence with one addition: a co-working requirements document should be an input to Phase 1 design, not just a later phase deliverable.

**On Ray's capacity concern:** He is right to name it. This is operationally more demanding than identity or passport. Legal exposure (DPAs, liability), compliance certs (SOC 2, ISO 27001), enterprise sales cycle (12–18 months in fintech), and security posture all require capacity we should be honest about not yet having. My view: name this openly in the brief to Mr. Ross, and propose that co-working is the destination that informs the earlier phase designs without necessarily requiring us to commit to a delivery date for Phase 2.5 today.

---

## Summary Position

Ray and I are substantially aligned. The key points where I add or diverge:

| Topic | Ray | Woodhouse |
|---|---|---|
| Revenue | Session fees + freemium | Session fees + freemium + tiered session types + attestation fees |
| TEE timing | Can defer to post-first-revenue | Must be genuine from first enterprise demo |
| Vertical wedge | Fraud/KYC continuous signal | Bounded joint investigation workflow specifically |
| Existential risk | Trust collapse as #1 | Trust collapse as #1, add cross-border data sovereignty as near-equal |
| Timing | Phase 2.5 | Phase 2.5 for pilot, but Phase 1 design must encode co-working requirements |

---

*Filed: /projects/agent-cowork/WOODHOUSE-ANALYSIS.md*
*Protocol: Independent draft before Ray collaboration — consensus synthesis to follow*

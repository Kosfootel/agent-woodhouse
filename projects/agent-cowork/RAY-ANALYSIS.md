# Agent Co-Working Space — Ray's Independent Analysis
**From:** Ray (.22) | **Date:** 2026-04-01 | **Status:** Independent — not coordinated with Liz
**Note:** CONCEPT_BRIEF.md was at a macOS path inaccessible from Ray's Linux node. Analysis built from Erik's description and first-principles reasoning from Agentcy.services work.
**Version:** Canonical (received via A2A 2026-04-01 ~01:11 EDT — supersedes prior draft)

---

## Q1 — Revenue Model

**Position: Session-based compute fees + tiered compliance add-on. Not per-message. Not seat licensing.**

The Stripe analogy cuts both ways. Stripe charges when a transaction completes — value is delivered at that moment. In agent co-working, the value moment is a **completed co-working session**: two agents collaborated, produced output, session closed. That's the unit.

Proposed structure:
- **Session fee** (metered on active co-work time, e.g. per-minute or per-session with floor): familiar to enterprise buyers who already pay for cloud compute this way. Predictable, auditable.
- **Compliance tier** (flat monthly add-on): audit logs, SOC2 attestation, data residency controls. This is the 'insurance product' enterprise security teams need to put you on an approved vendor list. Priced as insurance, not usage.
- **Identity anchoring fee** (if integrated with Agentcy.services passport): per verified agent identity registered on the platform, recurring. Scales with customer's agent fleet, low per-unit.

What to avoid:
- **Per-message**: perverse incentive to minimize platform use, hard to forecast, feels like a taxi meter
- **Seat licensing**: penalizes agent fleet growth, wrong signal for a platform that benefits from more agents
- **Data volume**: encourages data minimization, which works against the platform's purpose

**Enterprise reality check:** SOC2 Type II is table stakes to even get on an approved vendor list. Budget 9-12 months and $30-50k for first audit. Design for it from day one, not as an afterthought.

---

## Q2 — Build vs Partner: TEE/Secure Execution

**Position: Cloud-native confidential compute. Abstract the layer ourselves. Do not build TEEs in-house. Not a close call.**

TEEs (Intel TDX, AMD SEV, AWS Nitro Enclaves) are hardware-level security primitives. Building them in-house means chip-level expertise we don't have, attestation engineering at $300k+/engineer/year, and certification overhead on top. That's a different company.

**The right stack:**
- **Execution layer:** AWS Nitro Enclaves or Azure Confidential Computing. Both are production-hardened, audited, and give enterprise buyers a name they recognize on the compliance form.
- **We build:** the orchestration layer above TEE — session lifecycle, the API surface agents call, the audit log format, the identity integration with Agentcy.services passport
- **We do not build:** the enclave runtime, attestation chain, or hardware root of trust

**Strategic point:** Our defensibility is not in the TEE implementation — any cloud provider can do that. It's in the **protocol for how agents negotiate trust, share context, and terminate sessions**. That's the moat. Build there, rent the rest.

**Phase 1 shortcut worth noting:** For early customers, real TEE may not be necessary. A well-scoped data sandbox with contractual isolation and full audit logging may be sufficient to get to first revenue. TEE becomes the differentiator when selling into regulated industries. Don't over-engineer trust before demand is validated.

**Partnership angle:** Frame as 'built on AWS/Azure confidential compute.' They want ecosystem proof points. We get enterprise credibility. Mutual interest.

---

## Q3 — Go-to-Market: Vertical and Fastest Path to First Payment

**Position: Financial services, specifically fraud/AML signal sharing. Entry via existing consortia, not cold enterprise sales.**

Why fintech:
1. **The problem already exists.** Banks compete but share fraud signals — currently through slow, expensive consortia (FS-ISAC, ACAMS). Agents can do this faster with better isolation guarantees. Immediate willingness to pay.
2. **Budget is non-discretionary.** Fraud/compliance spend doesn't get cut in a downturn. A platform that reduces fraud losses by even 0.1% saves a mid-size bank tens of millions.
3. **Regulatory environment is a tailwind.** DORA, GDPR, and anti-money-laundering frameworks mandate data handling practices that a neutral trusted intermediary satisfies more cleanly than bilateral integrations.
4. **Consortia are warm leads.** ACAMS, FS-ISAC, SWIFT already have member orgs paying dues for exactly this kind of shared intelligence. Pitch to the consortium itself, not individual banks — short-circuits a 12-18 month enterprise sales cycle to 3-6 months.

**Fastest path to first paying customer:**
1. Identify one existing informal agent data-sharing arrangement (they exist — LinkedIn DMs, Slack groups, side channels at conferences)
2. Build a POC around their exact use case — probably: two agents compare signals on a shared dataset without exchanging raw data
3. Charge for the pilot. $5-10k/month is a real paying customer.
4. Use that reference to close the next five.

**Founder-led sales, not PLG.** This is not a product a developer spins up on a free trial. The first 10 customers need trust built personally. The Stripe founders literally drove to companies and installed it. Same playbook applies here.

---

## Q4 — Protocol Alignment: A2A / MCP / AGNTCY

**Position: Complementary infrastructure, one layer above existing protocols. Additive, not competitive. Standards-body is a Phase 4 play.**

Current landscape:
- **A2A (Google):** Agent-to-agent task delegation. Handles the communication channel, not cross-org trust or shared workspace.
- **MCP (Anthropic):** Tool and resource access protocol. Context provisioning, not collaboration.
- **AGNTCY (Cisco/Linux Foundation):** Discoverability and routing. Finding agents, not hosting their collaboration or brokering trust.

The co-working space fills a gap none of these address: **cross-organizational trust + neutral shared workspace for agents that don't natively trust each other**. It's not a competitor — it runs *on top of* the existing stack.

How it fits:
- Accept A2A messages natively as session entry points
- Expose workspace resources as MCP endpoints so agents can consume them with existing tooling
- Register sessions as discoverable units via AGNTCY-compatible metadata

This makes us the 'glue layer' — additive to all three. The neutral-party positioning is actually structural: Google can't be the trusted third party for a session involving Google agents. Microsoft can't either. We can.

**Watch closely:** AGNTCY is the closest overlap to our Phase 1-3 identity/passport/registry work. Either partner early or differentiate hard on the trust-intermediary vs identity-provider angle before they expand scope.

**Standards-body timing:** Not yet. You need 3-5 real enterprise implementations before any body takes you seriously. This is Phase 4.

---

## Q5 — Risk: Biggest Existential Threat

**Position: Not technical. The trust model collapsing — from breach, perceived bias, or regulatory seizure.**

The entire product rests on being provably neutral. Unlike Stripe (where trust is about money and fraud detection), here trust is about **strategic information**. The paranoia threshold is much lower. One incident of data leakage, perceived favouritism, or government seizure and the category becomes radioactive — not just us.

Specific failure modes in descending order of severity:

1. **A security breach exposing one participant's data to another.** This is the kill shot. The trust model has zero tolerance. Plan for it technically (TEE, audit logs) and legally (liability frameworks, incident response runbooks) from day one.
2. **Perceived bias.** Even without a real breach — if Participant A believes the platform is logging more of their data than Participant B's, or giving asymmetric access, they leave and tell their network. Neutrality must be *provable*, not just claimed. Technical proof > contractual promises.
3. **Regulatory seizure.** Data held in the platform becomes subject to discovery, subpoena, or government access in a cross-jurisdictional context. Every participant's confidential collaboration is exposed. Legal structure needs to address this before launch in regulated verticals.
4. **Hyperscaler commoditisation.** Microsoft and Google already have the infrastructure. If they ship 'secure multi-org agent collaboration' as a feature of Copilot or Vertex — which they could — they undercut the platform at zero marginal cost to buyers. Our counter: they can't be the neutral party in sessions involving their own agents. That's structural. But we need defensible customer relationships before that ship date.

**Secondary but worth naming:** No real demand. Cross-org agent collaboration may be a solution in search of a problem at this stage of the market. Validate demand before heavy investment.

---

## Q6 — Timing: Phase 3.5 or Does This Reprioritize Earlier Phases?

**Position: Phase 3.5 is roughly right, but the real dependency is Phase 1 (Identity) not Phase 3 (Registry). Phase 1 must be designed with multi-org federation in mind from day one.**

The co-working space requires:
- **Agent identity (Phase 1)** — you need to know who's in the room and authenticate them
- **Agent passport (Phase 2)** — portable, verifiable claims about capability and authorization
- **These are hard dependencies.** You can't verify participants without them.

What it does NOT strictly require:
- **Registry (Phase 3)** — discovery is useful but co-working sessions can bootstrap manually or bilaterally. Registry becomes the *distribution channel* for co-working, not a prerequisite for it.

**My recommendation: consider Phase 2.5, not 3.5.**

Once identity and passport are live, you have everything needed for a minimum viable bilateral co-working session. Don't wait for a full public registry before validating the collaboration model. First paying customers come via founder-led sales anyway — the registry accelerates at Phase 3/4 when you're going from 10 customers to 100.

**What this changes about Phase 1 (important):**
Identity layer must be designed with **multi-org federation** in mind. If Phase 1 builds a single-tenant system, retrofitting it for cross-org trust later requires breaking changes. The Phase 1 RFC needs to specify:
- Identity anchoring that works across organizational boundaries
- Attestation format verifiable by a neutral third party
- Permission scoping with selective disclosure (prove I'm a verified agent without revealing my full system state)

This is a design constraint to capture now, not a scope expansion that delays Phase 1.

**Phase 0 still correct.** Mesh-memory performance is the right first move. We can't build credibly on a broken foundation. But Phase 0 work is also field research for Phase 3.5/2.5 — we're learning what shared memory across agents actually looks like in practice.

---

## Summary

| Question | Ray's Position |
|---|---|
| Revenue | Session fees + compliance tier + identity anchoring. Not per-message. |
| TEE | Cloud-native (AWS Nitro/Azure). Abstract it. Don't build. |
| GTM | Fintech fraud/AML consortia. Approach the consortium body first. Founder-led. |
| Protocol fit | Additive above A2A/MCP/AGNTCY. Not competitive. Standards-body is Phase 4. |
| Existential risk | Trust model collapse: breach, perceived bias, or regulatory seizure. TEE + audit logs are existential, not features. |
| Timing | Lean toward 2.5 not 3.5. Phase 1 identity design must be multi-org federation aware from day one. |

**One concern outside the six questions:** Operational complexity. Co-working space requires security infrastructure, legal frameworks (DPAs, liability), compliance certifications, and enterprise sales motion simultaneously. It's the most operationally demanding product in the stack. Be honest in the synthesis about what execution actually requires — this isn't a product you can ship with three agents and no legal counsel.

— Ray

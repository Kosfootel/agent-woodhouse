# Agent Co-Working Space — Woodhouse Independent Analysis
**Date:** 2026-04-01
**Status:** Draft — pre-synthesis, pre-Liz. Filed before viewing Ray's positions.
**Note:** Analysis based on CONCEPT_BRIEF.md at /projects/agent-cowork/CONCEPT_BRIEF.md

---

## The Concept, As I Understand It

A neutral hosted platform — a "bonded warehouse" — where agents from competing or unrelated organisations can collaborate against shared data without either side exposing their full systems. The trust model borrows from Stripe: a credible third party holds the trust relationship so participants don't need to trust each other directly. Proposed as Phase 3.5 in the Agentcy.services build sequence.

My framing: this is a **custody product**, not merely a communications product. That distinction matters for every question below.

---

## Six Questions — Woodhouse's Analysis

---

### 1. Revenue Model

**My position: Tiered annual subscription per workspace, with a consumption overlay. Not pure session-pricing.**

The instinct to model on Stripe is correct, but there's a critical difference. Stripe processes transactions and releases them — it doesn't *hold* anything. A co-working space is a custody product: during an active session, we hold data. That changes the economics.

**Why pure session-pricing is risky:**
Enterprise procurement is built around predictable annual spend. A finance or legal buyer cannot take a variable-consumption product to their CFO. The first 10 customers will be enterprise; their needs must set the pricing architecture, not a hypothetical self-serve developer tier that doesn't exist yet.

**Recommended structure:**
| Tier | Pricing | Buyer |
|------|---------|-------|
| Pilot | Free (time-limited, N sessions) | Design partner validation |
| Standard | Annual flat fee per workspace | SME / founder-led |
| Enterprise | Annual per workspace + usage overlay | F500, regulated industries |
| Enterprise+ | Custom contract + SLA, audit, compliance certs | Banks, healthcare systems |

The usage overlay (above a baseline) aligns incentives at scale without making the base cost unpredictable. Usage is defined as compute-hours in a session, not data volume.

**One structural point:** TEE instances (required for the trust model) cost 2–3× standard compute. This is not trivial. Session fees and annual pricing must bake in the real infrastructure cost, not standard cloud compute rates. This is where most infrastructure companies miscalculate unit economics at launch.

**The identity-billing link:** Once Phase 1 identity and Phase 2 passport are live, session attribution becomes automatic — billing is trivial. Design the pricing model now with that assumption baked in, even if the early implementation is manual.

---

### 2. Build vs Partner — TEE / Secure Execution

**My position: Cloud-native, abstracted from day one, with a very precise interface contract. The abstraction is the product.**

I agree that building TEE from scratch is not viable for a company our size. The operational burden — attestation protocols, key management, supply chain verification, HSM provisioning — is a full engineering organisation. We are not that company.

**Cloud-native path:** AWS Nitro Enclaves, Azure Confidential Computing, or GCP Confidential VMs. These are production-hardened and available at commodity rates.

**My addition to the standard recommendation — the abstraction contract must come first.**

The temptation will be to build on Nitro Enclaves and let AWS abstractions leak into our data model. If the data access patterns, session lifecycle, and attestation model are Nitro-shaped, a provider switch is a rewrite, not a configuration change. We've seen this before with vendor lock-in: when the abstraction is an afterthought, it becomes load-bearing architecture.

**Protocol:** Design the provider interface contract (what our platform asks of a TEE, not how Nitro works) *before* writing the first AWS call. This is a one-sprint investment that buys indefinite provider optionality.

**Early shortcut (Phase 2.5 specific):** For the first bilateral co-working sessions — particularly in a founder-led, manually-brokered pilot — a well-scoped sandboxed environment with contractual isolation, audit logging, and human-reviewed consent gates may satisfy the buyer's trust requirement. TEE becomes the upsell for regulated industries and the credibility marker for enterprise. Don't delay launch for TEE readiness if the first customer doesn't require it. But don't promise TEE without it.

---

### 3. Go-to-Market — Vertical and First Paying Customer

**My position: Fintech (fraud / AML consortiums), founder-led, with a very specific definition of what "first paying customer" validates.**

Fintech is the right vertical. The forcing function is structural: AML, fraud detection, and credit risk all involve cross-institutional data sharing that is *legally required* in some jurisdictions and *competitively avoided* in practice. That tension is exactly the problem a neutral trusted third party resolves. The budget exists and the compliance case writes itself.

**Why not healthcare:** HIPAA Business Associate Agreements add legal overhead we are not ready to absorb. Healthcare is a Phase 3/4 vertical, not Phase 2.5.

**Why not legal:** Acute pain, but conservative procurement. Sales cycles 12–18 months with no predictable close. Wrong for early validation.

**The manual first relationship — a critical refinement:**

Ray's point about brokering the first relationship manually is correct. But "validate the model" is too vague. We need to define what we're validating with the first paid customer:

1. **Technical validation:** Two agents from different companies can exchange data in a shared workspace and produce a result neither could produce alone
2. **Trust validation:** Both parties will accept the platform as neutral without requiring full source code audit (i.e., trust can be established via contractual + operational means)
3. **Commercial validation:** Someone will pay, at a price point that covers TEE compute costs with margin

All three must be confirmed before we commit engineering resources to Phase 2.5 at full scale. The first customer is an experiment, not a launch.

**Acquisition motion:** Identify two fintech companies that are already trying (and failing) to collaborate on fraud signal. Introduce them. Run the session manually. Charge for facilitation. That is the Stripe playbook: the Collisons installed it themselves.

---

### 4. Protocol Alignment — A2A / MCP / AGNTCY

**My position: Complementary, not competitive — the co-working space is the assembly point for protocols that currently have no shared venue.**

Current protocol landscape:
- **A2A (Google):** Task delegation channel. Handles the communication mechanism, not the data trust layer.
- **MCP (Anthropic):** Tool and resource access. Context provisioning within a session, not across organisations.
- **AGNTCY (Cisco/LF):** Discoverability and routing. Finding agents, not hosting their collaboration.

None of these provide the thing this platform provides: **a governed shared workspace where agents from different trust domains operate against jointly-permitted data**.

This is not a competitor to any of them. It is the missing assembly layer.

**Positioning:**
- Accept A2A messages as native entry points into a session
- Expose workspace resources as MCP endpoints — agents use existing tooling to consume them
- Register sessions as discoverable units via AGNTCY-compatible metadata

This makes the co-working space the "landing zone" that existing protocols route to, not a replacement for them.

**One standards angle worth pursuing:** W3C Decentralized Identifiers (DIDs) and Verifiable Credentials (VCs) are directly applicable to agent identity verification at the workspace entry gate. Anchoring Phase 1 identity to VC/DID standards (rather than a proprietary scheme) would give the platform standards-body legitimacy that reinforces the neutrality claim. Worth exploring before Phase 1 is too far along to change.

**Competitive risk:** Google or Anthropic extending A2A/MCP to include the trust layer is real. The structural defence is neutrality: neither party can be the trusted third party when their own agents are participants. That holds as long as we can maintain genuinely neutral positioning. It doesn't hold if we're perceived as biased toward any participant's platform.

---

### 5. Risk — Existential Threats

**My position: Liability exposure is the highest existential threat. Breach is recoverable. Liability from a regulatory action against a held session is not.**

Ray's "who watches the watchmen" framing is correct and the specific failure modes are well-identified. I want to surface one that sits above all of them.

**The liability problem:**

Stripe made a deliberate choice to accept liability for fraud prevention — they built the chargeback infrastructure, the dispute resolution, the compliance certifications. That liability acceptance is a large part of why merchants trust them. It is also why Stripe's legal and compliance cost base is enormous.

A co-working space that hosts agent sessions containing strategic commercial data faces a question we must answer before we sign the first contract: **when an agent session results in harm, who is liable?**

- Data misuse (Company A's agent accesses data it shouldn't have)
- Competitive intelligence leak (data shared in a session appears in a competitor's product)
- Regulatory violation (a session processes data in a way that violates GDPR or CCPA)
- AI-generated harm (an agent in a session takes an action that causes financial or reputational damage)

If liability falls on the platform, we are carrying insurance and legal exposure that could dwarf engineering costs. If liability falls on participants, our contracts must be so tight that enterprise legal teams will kill adoption.

This is not unsolvable — it is the same problem legal escrow services and custodian banks have solved. But it requires a legal architecture designed in parallel with the technical architecture, not retrofitted after the first customer signs.

**Ranking of existential threats:**
1. **Liability from a regulatory action against a held session** — most severe, least recoverable
2. **A breach** — severe, but companies have recovered from breaches; recovery depends on transparency and response speed
3. **Neutrality perception failure** — if we are perceived as biased, trust collapses and is very hard to rebuild
4. **Cloud provider builds this natively** — real threat, but timeline gives us runway; defensibility is neutral positioning they structurally cannot claim

**Mitigation for #1:** Draft the data processing agreement and liability allocation framework before launching the pilot. Do not launch on a handshake.

---

### 6. Timing — Phase Sequencing

**My position: Phase 2.5 is directionally correct. The Phase 2 (passport) work should be scoped with co-working as the explicit first consumer.**

The true dependency chain for a minimum viable co-working session:

**Required:**
- Agent identity (Phase 1) — you cannot admit an unknown agent to a governed workspace
- A minimal claims/authorization layer (part of Phase 2) — you need to know what an agent is permitted to access before giving it access

**Useful but not required:**
- Full public registry (Phase 3) — discovery is nice; bilateral introductions work for the first 10 customers
- Full passport portability (Phase 2 complete) — portable claims are useful; manually-issued, platform-scoped credentials can stub this for the pilot

**The important reframe:**

Passport (Phase 2) risks becoming a beautiful abstract infrastructure component that takes 18 months and serves no immediate user story. If we scope Phase 2 as "build the thing that lets agents into the co-working space" rather than "build a general portable agent credential system," it stays grounded, ships faster, and produces something billable.

**Recommended revised sequence:**
```
Phase 0: Mesh debt clearance (current)
Phase 1: Identity layer (agent DIDs, authentication)
Phase 2: Passport — scoped as "co-working entry credential"
Phase 2.5: Co-Working Space MVP (bilateral, invite-only, founder-led)
Phase 3: Registry (discoverability + marketplace mechanics)
Phase 4: Distribution (unified platform pitch)
```

This is substantively close to Ray's recommendation. The difference is emphasis: Phase 2 must be consumer-driven, not specced in the abstract.

---

## Summary — Woodhouse's Position

| Question | My Position |
|----------|-------------|
| Revenue | Tiered annual subscription + compute-overlay; enterprise-first pricing; TEE costs must be in the model from day one |
| TEE | Cloud-native (AWS Nitro), but write the provider interface contract first; abstraction is the product |
| GTM | Fintech (AML/fraud), founder-led; first customer must validate all three gates (technical, trust, commercial) |
| Protocol fit | Assembly layer above A2A/MCP/AGNTCY; anchor identity to W3C VC/DID for standards legitimacy |
| Existential risk | Liability exposure from regulatory action against held session — design legal architecture in parallel with technical |
| Timing | Phase 2.5 correct; scope Phase 2 passport as co-working entry credential, not abstract infrastructure |

---

## One Concern Beyond the Six Questions

**Legal architecture is not a Phase 3 problem.**

A platform sitting between two companies as a trusted third party, holding their strategic data, is a legal entity with specific obligations. Data processing agreements, liability allocation, indemnification clauses, and regulatory certifications (SOC 2 Type II at minimum; likely ISO 27001 for regulated industries) must be designed in parallel with the technical architecture — not retrofitted when the first enterprise buyer's legal team asks for them.

This is the piece most technically-oriented founding teams defer until it blocks a deal. By then, the DPA they're forced to sign under pressure is wrong for them. The time to design the legal wrapper is Phase 1 or Phase 2, not Phase 2.5 launch.

Capacity concern noted: this product demands security infrastructure, legal frameworks, compliance certifications, and an enterprise sales motion running concurrently. That is operationally demanding at a standard befitting the trust model we're proposing to provide. We should be honest with Mr. Ross about what full execution requires.

---

*Filed: /projects/agent-cowork/woodhouse-independent-analysis.md*
*Next step: Request Liz's independent analysis, then synthesise all three.*

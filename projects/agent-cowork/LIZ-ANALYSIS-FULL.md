# Agent Co-Working Space — Liz's Full Independent Analysis
**Date:** 2026-04-01 ~01:xx ET
**Status:** Full independent analysis — no coordination with Ray
**Received by Woodhouse:** 2026-04-01 01:04 EDT (via A2A)
**Note:** Condensed summary also filed at LIZ-ANALYSIS.md (received 00:57 EDT). See RECONCILIATION section below.

---

## Q1. Revenue Model — Right pricing structure for enterprise buyers?

**Short answer:** Consumption-based pricing is the right foundation, with a trust-tier overlay.

The Stripe analogy is apt and instructive — Stripe charges per-transaction (not per-seat), which aligned incentives perfectly with usage patterns and made the cost legible to engineering teams. Agent co-working should follow the same structure:

**Recommended model:**
- **Session-based unit pricing** — charge per "co-working session" (defined as a bounded interaction between ≥2 agents against shared data). This is measurable, predictable, and mirrors the value delivered.
- **Data escrow tiers** — flat monthly fee for the trust infrastructure layer (key management, isolation environment, session logging). This covers the fixed cost of running the TEE/execution environment.
- **Compliance tier uplift** — enterprise buyers in regulated verticals (fintech, healthcare, legal) pay a premium for audit trail, attestation reports, and contractual liability allocation. This is where margin lives.

**What NOT to do:**
- Seat-based pricing doesn't translate — agents aren't people, and enterprises spin them up dynamically
- Pure pay-per-API-call is too granular; it confuses procurement and creates friction
- "Platform fee" subscription-only loses the upside as usage scales

**The trust premium is real.** Stripe's moat wasn't cheapness — it was "I don't have to worry about this." Price accordingly. Enterprise compliance uplift should be 3-5x the base tier. Don't undercharge for the liability you're absorbing.

---

## Q2. Build vs Partner — TEE/secure execution?

**Short answer:** Cloud-native confidential compute first, with a hard ceiling on how long we stay there.

The options ranked:

1. **Cloud-native confidential compute (Azure Confidential Computing, AWS Nitro Enclaves, GCP Confidential VMs)** — START HERE
   - Lowest time-to-market by far
   - Existing enterprise trust anchors (SOC 2, ISO 27001 already present)
   - The "trusted third party" story is actually *strengthened* by running on infrastructure enterprises already audit
   - Risk: we are dependent on hyperscaler roadmap and pricing; they could undercut us with a native offering

2. **License from TEE specialist (Anjuna, Edgeless Systems, etc.)** — MIDDLE PATH
   - Better portability across cloud providers
   - Meaningful cost reduction vs raw cloud confidential compute at scale
   - Good option at Series A stage when customer contracts justify the complexity
   - Not for Day 1 — integration burden is real

3. **Build in-house** — DO NOT DO THIS BEFORE PRODUCT-MARKET FIT
   - TEE hardware expertise (SGX, TrustZone, RISC-V PMP) is a 3-5 year moat, which is also a 3-5 year distraction
   - The value prop to customers is *neutral ground*, not *novel hardware* — don't confuse the two
   - Revisit at Phase 4 / Scale if hyperscaler lock-in becomes a genuine strategic risk

**The framing risk I'd flag:** "Build TEE in-house" can easily become the thing the engineering team falls in love with because it's technically interesting. Keep the north star: the moat is trust architecture and network effects, not cryptographic hardware.

---

## Q3. Go-to-Market — Which vertical first, fastest path to a paying customer?

**Short answer:** Financial services. Specifically: fintech-to-fintech agent collaboration where both parties have compliance mandates preventing direct data sharing.

**Why financial services:**
- They *already understand* the trust-intermediary model — they live with SWIFT, Visa, DTC, and other trusted clearinghouses every day. The concept maps onto mental models they already hold.
- The problem is live now: fraud detection agents from two banks can't share signals because data never leaves the org. A neutral session-level exchange would be immediately valuable.
- Procurement is slower than a startup, but they will actually sign contracts and pay enterprise prices. They are not tire-kickers.
- Compliance uplift pricing (Q1) is not a hard sell here — it's table stakes.

**The fastest path to a first paying customer:**
1. Identify 2 mid-tier fintechs (not Big 4 banks — too slow) with adjacent but non-competing agent use cases (e.g., credit decisioning + fraud flagging)
2. Offer a **design partnership** — we build the first co-working session together, they pay a nominal fee that converts to contract
3. Use that session as the attestation proof point for the next 5 sales

**Alternatives considered and ranked:**
- Healthcare (too much HIPAA-specific legal overhead up front)
- Legal/IP (good second vertical — real need for neutral ground in M&A data rooms — but slower sales cycle than fintech)
- Supply chain (agent-to-agent collaboration is less mature here; the buyers are less ready)

**One contrarian thought:** the fastest path to *any* paying customer might be mid-market SaaS companies with AI features, not enterprise at all. They have budget, they move fast, and they are already building agent-to-agent workflows. The risk is the revenue per customer is lower. Worth a separate POC track if enterprise proves slow.

---

## Q4. Protocol Alignment — A2A/MCP/AGNTCY fit?

**Short answer:** This is not adjacent to those protocols — it is the *trust layer beneath them*. That's a different and stronger position.

**A2A (Agent-to-Agent Protocol):** A2A defines how agents exchange messages and tasks. Agent Co-Working Space is the *neutral infrastructure where A2A sessions are brokered between untrusted parties.* It's a hosting layer, not a competing protocol. Framing: "A2A-native execution environment for cross-org collaboration."

**MCP (Model Context Protocol — Anthropic):** MCP defines how models access external tools and data. Co-Working Space can expose a *shared MCP context* that both agents access within the session boundary — this is a direct product integration opportunity, not a conflict.

**AGNTCY (the Linux Foundation agent interop effort):** This is the most important alignment play. AGNTCY is attempting to standardize agent discovery and interoperability at the ecosystem level. Agent Co-Working Space should:
1. Implement AGNTCY-compliant session brokering (legitimacy signal to enterprise buyers)
2. Contribute to AGNTCY working groups on trust/security architecture (becomes a de facto reference implementation)
3. Use standards-body participation as a lead-gen channel — the people in those rooms are the enterprise buyers

**The partnership angle I'd pursue first:** Approach either the Google Cloud or Microsoft Azure agent teams. They are building the cloud-side of A2A adoption and need a trust layer story. A partnership gives cloud distribution + enterprise trust without us having to build the sales motion from scratch.

---

## Q5. Risk — Biggest existential threat?

**Short answer:** A hyperscaler builds this as a native feature.

Azure already has Confidential Ledger. AWS already has Clean Rooms (for data collaboration). The pattern of "neutral ground for parties who don't trust each other" is not novel to cloud vendors.

**The specific threat:** AWS launches "Agent Clean Rooms" — a managed service that lets agents from different AWS accounts collaborate against shared data within a Nitro Enclave, billed as an AWS service. Done. Our addressable market collapses.

**Why it hasn't happened yet:** The agent collaboration problem is too new for their product planning cycles. We have 12-24 months of window, possibly more.

**Secondary existential risks (in order):**
1. **Trust incident** — a breach of the execution environment, even a small one, destroys the product permanently. Trust businesses have no second chance. Security must be over-engineered, not right-sized.
2. **Adoption chicken-and-egg** — if the two-sided network never bootstraps (no agents want to co-work because no counterparties are on the platform), the product dies in design partnership limbo
3. **Protocol monoculture** — if one A2A implementation (e.g., Google's) becomes so dominant that they also own the trust model, the "neutral ground" value prop erodes

**What the hyperscaler threat implies for strategy:**
- Move fast on the network effect (Phase 3 → Phase 3.5 needs to compress)
- Get enterprise contracts signed before the cloud vendors have a competing product in preview
- The moat is not the TEE — it's the trust architecture, the policy framework, and the two-sided network. Build those aggressively.

---

## Q6. Timing — Is Phase 3.5 correct, or does this change earlier phase priorities?

**Short answer:** Phase 3.5 is the right *position* in the sequence, but the identity layer (Phase 1) needs to move faster because it's a prerequisite — not a precursor.

**The dependency chain:**
```
Phase 1: Identity layer (agent passport) 
   → required to verify "who" is in the session
Phase 2: Portable memory 
   → required to give agents shared context without full system exposure
Phase 3: Registry/discovery 
   → required to find counterparties
Phase 3.5: Co-Working Space 
   → consumes all of the above
```

The Co-Working Space *cannot ship without Phase 1*. An agent session with no cryptographically verified identity is just two black boxes talking — the trust story falls apart immediately under enterprise due diligence.

**What this means for earlier phases:**
- **Phase 0 (mesh fixes):** Unchanged — must ship. Blocking.
- **Phase 1 (identity layer):** ACCELERATE. This was always important; it's now critical-path for the Co-Working Space concept. The identity spec needs to be tight, not "good enough for the mesh."
- **Phase 2 (portable memory):** Can run in parallel with Phase 1 but should not block Co-Working Space design work starting.
- **Phase 3 (registry/discovery):** Co-Working Space is actually a natural forcing function to get Phase 3 right — the discovery problem for "who can I co-work with" is the same registry problem, but with trust requirements. Don't design them separately.

**The case for pulling Co-Working Space earlier than Phase 3.5:**
The concept is strong enough to raise a seed/pre-seed on the narrative alone, before the technical stack exists. Build-in-public and investor-facing messaging on this concept should start *now*, not at Phase 3.5. The actual *product* ships at 3.5. The *story* should be live within weeks.

**Summary timeline recommendation:**
- Now: file concept brief, start build-in-public narrative, investor conversations
- Phase 1 accelerated: identity layer in 60-90 days
- Phase 3: registry design incorporates Co-Working Space discovery requirements from day one
- Phase 3.5: product in market, first design partnerships signed

---

## RECONCILIATION NOTES (filed by Woodhouse)

The condensed analysis (LIZ-ANALYSIS.md, received 00:57 EDT) differs from this full analysis in two meaningful respects:

1. **GTM sequence:** The condensed version recommended mid-market SaaS first; the full analysis recommends financial services first, with mid-market SaaS as a "contrarian thought / separate POC track." These are reconcilable — the full analysis is the deliberate position.

2. **Timing:** The condensed version recommended Phase 2.5; the full analysis confirms Phase 3.5 as the correct slot, but with Phase 1 accelerated. This aligns with Ray and Woodhouse's positions.

The CONSENSUS-BRIEF.md has been updated accordingly (see separate update note).

---
*— Liz 🐿️ — Full independent analysis, no coordination with Ray*
*Filed by Woodhouse at LIZ-ANALYSIS-FULL.md*

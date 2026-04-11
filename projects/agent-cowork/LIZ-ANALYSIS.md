# Liz — Independent Analysis: Agent Co-Working Space
*Received: 2026-04-01 01:05 EDT | Filed by Woodhouse for synthesis*
*Written independently before seeing Ray's response, per Erik's instructions*

---

## 1. Revenue Model — Right Pricing Structure?

Three candidates:

**A. Per-session / per-collaboration event** — charge when two agents spin up a shared context. Risk: enterprises will aggregate every interaction into a single long "session" to minimize charges.

**B. Seat + usage hybrid (Stripe-like)** — flat monthly per-tenant fee plus metered usage on compute-intensive operations (secure execution time, attestation events, audit log storage). Long-term target. The "transaction" is the attestation or secure execution event, not the raw message.

**C. Data escrow SaaS** — flat per-seat fee. Predictable revenue, lower friction for enterprise pilots. Better for Phase 1 land-grab; wrong long-term structure.

**Recommendation:** Start with C for early pilots. Build toward B from day one — that's the moat. The meter that matters is attestation events and secure execution time, not API calls.

Contrarian note: if this becomes infrastructure, pricing power is inherently limited. Price premium before the market commoditizes it.

---

## 2. Build vs Partner — TEE/Secure Execution

**Build it:** Full control, years of eng, significant capital. TEE landscape not converged (ARM CCA vs Intel TDX vs AMD SEV-SNP). Stranded abstraction risk.

**License it:** Existing vendors — Anjuna, Edgeless Systems, Fortanix, Opaque Systems. Time-to-market advantage, lets us focus on trust/identity layer. Vendor dependency, margin compression.

**Cloud-native (AWS Nitro, Azure Confidential, GCP Confidential Space):** Lowest barrier, best enterprise credibility. Risk: locked to cloud provider, contradicts "neutral ground" positioning.

**Recommendation:** Cloud-native for POC and first enterprise pilots. License a vendor abstraction layer for MVP. Build ONLY the trust coordination layer ourselves — attestation routing, session management, dispute protocol. Never build the TEE runtime.

Cloud-native neutrality problem is solvable: multi-cloud deployment (AWS AND Azure AND GCP simultaneously). Reframe "neutral" as "portable" — enterprises understand that framing.

---

## 3. Go-to-Market — Which Vertical First?

**Financial services (Phase 1 enterprise target):**
- Concrete use case: two banks' agents collaborating on shared customer (fraud, loan origination, portfolio reconciliation)
- Regulatory framework (GLBA, OCC) actually helps — regulators want third-party trust intermediary for inter-institution exchange
- Procurement cycles long (18–24 months) but pilots move faster with regulatory hook
- "Stripe" analogy lands instantly in fintech

**Healthcare:** Skip for now — FDA/HIPAA compliance overhead delays time-to-first-dollar 12+ months.

**Fastest path to paying customer:** Mid-market SaaS with existing partner ecosystem — 3–5 partner integrations where their agent needs to talk to a vendor's agent. No GLBA overhead, thinks natively in API terms, desperate for agent-equivalent of OAuth.

**GTM sequence:** Mid-market SaaS partner ecosystems → case study → finserv enterprise motion.

---

## 4. Protocol Alignment — A2A/MCP/AGNTCY Fit

**A2A (Google):** Strong alignment. Co-working space is the trust layer making A2A safe in production. Be A2A-native: any two A2A-compatible agents should initiate a co-working session without additional integration.

**MCP (Anthropic):** Lower direct relevance (tool/resource access, not agent-to-agent trust). Angle: co-working space as MCP server — "context provider" supplying agents with shared ground truth. Opens distribution through existing MCP ecosystem.

**AGNTCY:** Strong alignment. AGNTCY finds agents; co-working handles what happens after they meet. Formal AGNTCY compatibility early = GTM accelerant.

**Explicit concern:** If we declare "neutral ground" but also build the Agentcy.services identity layer (Phases 1–2), there's an implicit conflict. Must architect as genuinely separate components — or own the "vertically integrated stack" positioning explicitly and defend it. Can't have it both ways quietly.

---

## 5. Risk — Biggest Existential Threat

**A — Commoditization by cloud providers.** 12–24 months if market signals strong. Mitigation: speed + network effects.

**B — Protocol capture.** A2A or MCP ships native trust/attestation primitives. Mitigation: embed in protocol development, contribute to specs.

**C — Liability when it breaks.** (Liz's pick — biggest existential threat)

The co-working space is the trust intermediary. A single high-profile incident (healthcare wrong clinical decision, financial material trading error) could be terminal before we have revenue to absorb legal exposure. The insurance/liability problem that killed early fintech middleware companies.

Required from day one:
- ToS scoping liability to "infrastructure, not outcomes"
- Legal entity structure shielding platform from consequential damages
- E&O insurance for tech infrastructure
- Must be in corporate structure at formation — not retrofitted after first lawsuit

A and B are competitive risks. C is existential in a way no amount of technical excellence can fix.

---

## 6. Timing — Phase 3.5 or Earlier?

Current approved sequence: Phase 0 → 1 → 2 → 3 → 4.

**Phase 3.5 is too late.** This should be Phase 2.5.

Logic: identity (Phase 1) and passport (Phase 2) are prerequisites. But the co-working space does NOT require a public registry (Phase 3). Two enterprises can use it with private, federated identity before any public discovery layer. Phase 3 may actually be downstream of 2.5, not upstream.

**Revised sequence advocated:**
- Phase 0: Mesh debt
- Phase 1: Identity layer
- Phase 2: Passport (portability)
- **Phase 2.5: Co-Working Space** — first real revenue, enterprise validation, stress-tests identity infra under real adversarial conditions
- Phase 3: Public registry (built on validated identity infra, not spec)
- Phase 4: Distribution (co-working space network IS the distribution channel)

Risk of moving earlier: committing to enterprise product before identity primitives hardened. A breach destroys trust in the entire Agentcy.services brand. POC/MVP gating still applies.

---

## Summary

1. Revenue: Start flat SaaS for pilots → metered attestation events. Premium pricing — trust is the moat.
2. Build/partner: Cloud-native POC + license TEE abstraction for MVP + build only trust coordination layer.
3. GTM: Mid-market SaaS first → finserv. Skip healthcare.
4. Protocol: A2A-native + MCP server interface. Neutrality/identity conflict needs explicit architectural answer.
5. **Existential risk: Liability when agent collaboration causes real-world harm. Corporate structure problem — not a tech problem.**
6. Timing: Phase 2.5, not 3.5.

---
*— Liz 🐿️*
*Full analysis received and filed 2026-04-01 by Woodhouse*

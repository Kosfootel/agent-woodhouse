# Agent Co-Working Space — Liz Independent Analysis (V3 / Final)
*Received via session relay — 2026-04-01 01:19 EDT*
*Filed by Woodhouse. This is Liz's third independent submission, arriving after CONSENSUS-BRIEF.md was filed at 01:15 EDT.*
*Note from Liz: CONCEPT_BRIEF.md was at a macOS path inaccessible from her machine. Working from prompt description.*

---

## 1. Revenue Model

Stripe analogy is useful but incomplete — Stripe prices the transaction; here the unit of value is the *trust relationship*, not data moved.

**Recommendation: base subscription + metered compute inside the secure space.**
- Base (per-org, not per-agent): covers identity verification, credentials, SLA, account mgmt. Enterprises can budget this.
- Metered: compute-seconds in the enclave, storage duration, session count. Variable, tied to value consumed.
- Avoid pure usage-only at launch — enterprise procurement needs a predictable floor. Committed base + burst overage works.

The moat isn't the compute — it's the trust establishment (vetting, credentialing, legal framework). *That's* what commands premium pricing.

Anchor: $5–25k/mo base by tier. Early design partners get flat fee for 12 months in exchange for shaping the product.

---

## 2. Build vs Partner — TEE

Don't build hardware TEE infrastructure. That's deep systems work, specialist expertise, funding cliff.

**Recommendation: cloud-native confidential compute first, specialist library second.**
- AWS Nitro Enclaves or Azure Confidential Computing (AMD SEV-SNP): production-ready, enterprise-audited. Nitro has the edge — it's where enterprise agents already run.
- For attestation layer: Edgeless Systems (Constellation/EGo) or Fortanix as specialist libraries — they abstract TEE APIs and add workload attestation.

**Honest caveat:** TEE solves the *technical* trust problem, not the *institutional* one (see Risk). Don't over-invest before validating that buyers care about the technical guarantee vs. the contractual one.

**Decision tree:**
1. POC: contractual trust + software isolation — fast, cheap, validates demand
2. MVP: cloud-native TEE (Nitro or Azure CC)
3. Product: specialist attestation library on top

---

## 3. Go-to-Market

**Pick: AI infrastructure / developer tooling companies first. Not healthcare, not finance.**

Reasons: they already speak A2A/MCP/TEE (no education overhead), pain is immediate and visceral (everyone is trying to partner with competitors' agents right now with no safe mechanism), sales cycles fast, small number of high-value first customers.

**Fastest path to paying customer: don't sell the platform. Find two companies with a specific shared-data problem and deliver the solution.** Build the platform as you deliver it. Second customer validates the abstraction.

Concrete use case: Company A has LLM-powered due diligence agent, Company B has proprietary financial data agent. They want joint analysis without exposing each other's signals. Real problem, real dollar value. Find that conversation.

---

## 4. Protocol Alignment

This concept lives in the **gap between A2A, MCP, and AGNTCY** — which is both the opportunity and the risk.

- A2A (Google): solves comms protocol, not multi-party trust or execution environments
- MCP (Anthropic): solves tool/context sharing within a session, not cross-org trust
- AGNTCY: closest in spirit — open agent network for discovery and interoperability

**Key position: this is infrastructure, not a protocol.** Don't compete with the protocols. Implement them as the communication layer *inside* the co-working space. Agents bring their existing integrations; the platform is the neutral container.

**Standards angle:** Nobody owns the spec for neutral execution environments with cross-org agent trust. Contributing to AGNTCY — or proposing a working group — establishes thought leadership before any competitor. Positioning move as much as technical.

**Partnership angles:**
- AGNTCY: most natural, least conflict risk
- Anthropic: MCP compat story + potential design partner
- Google: A2A compat story — but they could build this themselves, be cautious

---

## 5. Risk — Biggest Existential Threat

**Not the cloud providers. The institutional trust gap.**

Stripe works because payments have a regulatory framework. Stripe operates within it; its trustworthiness is partly regulatory. Agent co-working spaces have no equivalent framework yet.

When an enterprise CISO asks 'why do we trust YOU as the neutral party?' — TEE attestation doesn't fully answer it. The question is institutional, not technical.

**The existential risk:** enterprise buyers may require institutional-grade trust (regulatory standing, consortium backing, big-name investors as guarantors) before they'll run sensitive agent workloads on an unknown platform.

The TAM is real. The risk is that trust gap requires either: (a) a major institution co-founding or acquiring to lend institutional standing, or (b) years of earned trust through track record.

**Mitigation:** design partners with credible names *become* the trust signal. Customer 1 and 2 need to be companies that other enterprises will trust by association. A Goldman or JPMorgan design partner makes every subsequent enterprise sale easier.

**Secondary risk:** bilateral integrations + point-to-point legal agreements eat the market. Companies solve trust via direct contracts and skip the neutral platform. This is how many third-party middleware plays die.

---

## 6. Timing — Phase 3.5

Phase 3.5 is **logically correct but commercially late**.

The logical dependency is real: you need agent identity (Phase 1) and discovery (Phase 3) before a proper co-working space. Agents need passports to enter and a directory to find each other.

**But the window may close before we get there organically.**

**Recommendation: keep Phase 3.5 in sequence, but add a Phase 1.5 market validation spike.**

Phase 1.5 spike:
- Two specific companies, hand-picked
- No registry/discovery — hardcoded participants
- Neutral execution env (Nitro or just contractual trust)
- One concrete shared-data use case
- Goal: validate enterprise willingness to pay *before* building everything upstream

If the spike yields a LOI or early contract → pull co-working concept forward, possibly to Phase 2. Identity/passport narrative gets a killer hook: 'here's why you need an agent passport — to enter the co-working space.'

If spike gets polite interest but no commitment → Phase 3.5 timing is correct, build toward it.

**Earlier phases unchanged. Phase 1.5 is additive — runs adjacent, doesn't displace Phase 0–3.**

---

*— Liz 🐿️*
*Received and filed by Woodhouse: 2026-04-01 01:19 EDT*
*Woodhouse reconciliation notes below.*

---

## Woodhouse Reconciliation Notes

**Deltas vs. LIZ-ANALYSIS.md (V1) and LIZ-ANALYSIS-V2.md (V2):**

| Topic | V1 position | V2 position | V3 position | Change |
|---|---|---|---|---|
| Revenue anchor | $1K–$5K/mo platform + per-session | Explicit pricing + audit log as distinct product | $5–25k/mo base + compute overlay; 12-month design partner flat fee | More specific; design partner model new |
| TEE approach | Cloud-native → abstraction layer | Anjuna (cloud-agnostic) short-term | Nitro/Azure CC + Edgeless/Fortanix; explicit decision tree | POC = contractual is *new and important* |
| GTM vertical | Mid-market SaaS first | Data vendors + quant/hedge; channel model | **AI infra / dev tooling first** | Significant shift — third distinct position from Liz |
| Use case | Two banks' agents, fraud | Data vendor as channel partner | LLM due diligence agent + proprietary data agent | New concrete example |
| Risk #1 | Liability when collaboration causes harm | Cloud providers eat us | **Institutional trust gap** | Material reframe — new primary risk |
| Risk (new) | — | Lighter trust model settles first | Bilateral integrations / middleware death pattern | New, important |
| Timing | Phase 2.5 (V1) / Phase 3.5 (V2) | Phase 3.5 confirmed | Phase 3.5 + **Phase 1.5 validation spike** | Genuinely new mechanism; most important addition |

**Items requiring amendment to CONSENSUS-BRIEF.md:**
1. Phase 1.5 validation spike — new concept not present in any prior analysis; merits explicit flagging to Mr. Ross
2. Institutional trust gap as primary risk — stronger framing than "liability" (Liz V1) or "cloud providers eat us" (Liz V2); should be added to risk register
3. Bilateral integrations / middleware death — secondary risk not previously named; worth including
4. AI infra / dev tooling as GTM entry point — Liz has now held three different positions on vertical. The three-agent summary should reflect that this question remains actively contested
5. Design partner flat-fee model — specific pricing mechanism ($5–25k/mo base, 12-month flat for early design partners) not previously incorporated

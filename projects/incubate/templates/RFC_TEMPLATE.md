# RFC-NNNN: [Short Title]

**Status:** Draft | Under Review | Accepted | Rejected | Superseded  
**Author(s):** [Agent or human name]  
**Created:** YYYY-MM-DD  
**Last Updated:** YYYY-MM-DD  
**Supersedes:** RFC-NNNN (if applicable)  
**Superseded by:** RFC-NNNN (if applicable)

---

## Summary

*One paragraph. What is this RFC proposing and why does it exist? Someone who hasn't read anything else should understand what's being decided after reading this.*

---

## Motivation

*Why does this change need to happen? What problem does it solve? What breaks or degrades if we don't do this?*

*Be specific. "We need to improve X" is not motivation. "When two agents send messages simultaneously to the same receiver, the relay drops the second message because the queue lock is not atomic" is motivation.*

---

## Prior Art / Existing Approaches

*What already exists — in our codebase, in the open source world, in published specs — that is relevant to this proposal? Have others solved this problem? What did they do?*

*This section is required. Skipping it is how we redesign things that already exist. If nothing relevant exists, state that explicitly.*

---

## Detailed Design

*The meat. Describe exactly what you are proposing. Include:*

- *API endpoints (if applicable): method, path, request schema, response schema, error codes*
- *Message formats (if applicable): field names, types, constraints, required vs optional*
- *Protocol flow (if applicable): sequence diagrams in ASCII or prose*
- *Data model changes (if applicable): what tables/files change and how*
- *Agent behavior (if applicable): what does each agent do differently*

*If the design is long, use subsections.*

### Example

*Provide a concrete example of the proposed change in action. Show a request/response, a message exchange, or a code snippet. Abstract descriptions without examples are hard to review.*

---

## Alternatives Considered

*List the approaches you considered and rejected. For each: what is it, why did you consider it, and why did you reject it? "We considered X but chose Y because Z."*

*Not having alternatives is a red flag that the design space wasn't fully explored.*

| Alternative | Why Considered | Why Rejected |
|-------------|---------------|--------------|
| ... | ... | ... |

---

## Impact Assessment

### Breaking Changes
*Does this proposal require existing agents to update their code or config before they can interoperate? If yes, describe the migration path.*

- [ ] No breaking changes
- [ ] Breaking change — migration path: [describe]

### Affected Components
*List every component, file, or service that needs to change if this RFC is accepted.*

- `component-name` — [what changes]
- ...

### Security Considerations
*Does this change the attack surface? Does it handle untrusted input? Does it expose new data to agents that shouldn't have it? Does it affect the privacy filter?*

### Performance Considerations
*Does this add latency? Does it change memory or disk usage? At what scale does it become a problem?*

### Twelve-Factor Considerations
*For Agentcy.services infrastructure: does this proposal align with Twelve-Factor principles? Does it introduce stateful in-process data that should be a backing service? Does it hardcode config?*

---

## Open Questions

*List things you haven't decided yet, things you're uncertain about, or things you want reviewers to specifically weigh in on.*

1. [Question]
2. [Question]

---

## Review Checklist

Before this RFC moves from Draft → Under Review:
- [ ] Prior art section is complete
- [ ] At least one concrete example is provided
- [ ] Alternatives considered section is complete
- [ ] Breaking changes explicitly called out
- [ ] Security considerations addressed

Before this RFC moves from Under Review → Accepted:
- [ ] All three agents have reviewed and commented
- [ ] Erik has approved
- [ ] Open questions are resolved or explicitly deferred
- [ ] Affected components list is finalized

---

## Decision

*Filled in when the RFC reaches Accepted or Rejected status.*

**Decision:** [Accepted | Rejected]  
**Decision date:** YYYY-MM-DD  
**Decided by:** [Names]  
**Rationale:** [Why this decision was made. If rejected, why. If accepted, any conditions or caveats.]

---

## Implementation Notes

*Filled in after acceptance. Track what was actually built vs. what was proposed. Any deviations from the design should be documented here with rationale.*

- Implementation PR/commit: [link]
- Deviations from design: [none | describe]
- ADRs created as a result: ADR-NNNN, ADR-NNNN

---

*Template version: 1.0 — Better Machine, 2026-03-31*

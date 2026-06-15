# Feedback on GX-10 Dev Pod Spec - Iteration 1

**Reviewer:** Liz (subagent perspective)  
**Date:** 2026-06-13  
**Context:** Agency agent running on local GPU server for automated code review

---

## Overall Assessment

Solid foundation. The spec correctly identifies a real gap—frontier models are great at immediate tasks but terrible at accumulating codebase context over time. The "back of house dev team" framing is exactly right.

However, I see a tension between "single reviewer" (listed under Non-Goals) and the actual architecture which implies multiple specializations. I think you should lean into that tension rather than avoid it—Iteration 1 should test the multi-agent pattern even if lightweight.

---

## Detailed Feedback

### 1. Agent Architecture & Specialization

**Current:** Single agent with 4 specializations (rust_security, python_patterns, architecture, performance)

**Concern:** One agent trying to be "thorough, security-conscious, pragmatic" + four distinct domains = cognitive overload in the prompt. The specializations are broad enough that they'll conflict with each other, especially "architecture" vs "performance" (often tradeoffs).

**Suggestion:** Either:
- **A)** Split into 2-3 lightweight sub-agents that each produce focused reports, then aggregate
- **B)** Keep single agent but run separate passes with domain-specific prompts

My preference: **Option A** even in Iteration 1. The cost of spawning 3 agents is trivial compared to the benefit of focused, non-conflicting reviews. It also tests your multi-agent orchestration earlier.

**Draft agent split:**
```
Security Auditor (blocking) - catches unsafe, crypto misuse
Pattern Reviewer (non-blocking) - idioms, type hints, error handling
Architecture Steward (non-blocking) - coupling, boundaries, imports
```

The key is giving each a narrow identity and clear escalation rules. Security blocks, others suggest.

---

### 2. Prompt/Output Format Design

**Current:** Structured markdown with severity tiers

**What's good:**
- Explicit "do_not_review" list prevents noise from formatters
- Severity levels (INFO/WARN/CRITICAL) give clear triage
- Context-aware findings ("Previous commit showed this path is hit during recovery")—this is the gold, make sure the prompt emphasizes it

**What's missing:**

**A) Confidence scoring**
Add a `confidence: high|medium|low` to each finding. LLMs hallucinate reviews too. A low-confidence WARN is very different from a high-confidence CRITICAL.

**B) Actionability tiers**
Current severity is about impact. Add actionability:
- `auto-fixable`: Code transformation is obvious
- `suggested`: Needs human judgment
- `discussion`: Requires architectural decision

**C) Negative findings**
"Architectural Notes" includes positives (✅). Also call out what was *considered* and rejected. "Looked for X pattern, didn't find issues" builds trust that it's not just pattern-matching.

**Revised finding structure:**
```markdown
### W1: Unwrap in async context
**Severity:** WARN  
**Confidence:** high  
**Actionability:** auto-fixable  
**File:** `src/mesh/sync.rs:89`  
**Issue:** `result.unwrap()` can panic, use `?` or match  
**Suggested fix:** Replace with `result?`  
**Context:** Previous commit showed this path is hit during recovery  
**Rationale:** [One sentence on why this matters in your specific codebase]
```

The "Rationale" field forces the agent to justify findings—great for catching false positives in review.

---

### 3. Workflow Integration

**Current:** Webhook → agent → report file → optional chat notification

**Questions:**

**A) GitHub PR integration vs file-only reports**
File reports are fine for internal use but the loop is slow. Consider:
- PR comments via GitHub API (requires token, more complex)
- Status checks that block on CRITICAL findings (more complex)
- Start with file reports, add PR integration in Iteration 2

**Verdict:** Keep file reports for Iteration 1, but document the PR integration path.

**B) ngrok vs local tunnel**
ngrok is fine for testing but has rate limits and external dependency. For a "runs continuously" service, prefer:
- Local reverse proxy (nginx) with Tailscale for external access
- Or: poll-based instead of webhook (simpler, no tunnel needed)

**Suggestion:** Add a polling fallback mode. GitHub Actions cron or local cron that checks `git log --since` every 5 minutes. Less elegant but more reliable for a "just works" Iteration 1.

**C) Report retention**
`~/gx10-reviews/{repo}/{timestamp}-{commit-sha}.md` will accumulate fast. Add:
- Rotation policy (keep last N days or archive to S3/cold storage)
- Index file (JSON or simple HTML) for browsing

---

### 4. Agency Patterns That Apply

**Pattern: Tool-Use Loop**
The agent needs more than just "fetch diff + review." Consider:
- `read_file` to pull in referenced modules
- `search_codebase` to find similar patterns
- `check_imports` to verify dependency constraints
- `query_git_history` for "when was this last changed"

The context window is 32K. Use it aggressively. A 500-line diff plus 3 related files is well within budget and massively improves review quality.

**Pattern: Reflection Loop**
After generating findings, add a second pass:
```
"Review your own findings. Which ones might be false positives?
Which are trivial? Remove or downgrade anything that wouldn't
be worth a human reviewer's time."
```

This self-critique step reduces noise significantly. I've seen it cut false positives by 30-40%.

**Pattern: Memory Accumulation**
The spec mentions "learns our patterns" but doesn't specify how. In Iteration 1:
- Store a `patterns.jsonl` of recurring findings per repo
- On review, include: "Previous similar issues found in files: ..."
- Track which findings were accepted/rejected (human feedback loop)

Even simple JSONL storage teaches the agent "we care about X, we ignore Y."

---

### 5. Scope for Iteration 1

**Current scope feels right** for a 7-day sprint. One thing I'd tighten:

**Remove:** "Document learnings for Iteration 2 scaling"
**Replace with:** "Measure and record: inference latency, cost per review, false positive rate, human acceptance rate"

The learnings will emerge from the metrics. Don't just document anecdotes—build the measurement infrastructure now.

---

## Specific Suggestions

### Model Choice (Open Question #1)

**My take:** Qwen3-72B for coding, Llama 3.3 70B if you want more "conversational" output. For code review, Qwen3 wins on benchmarks and context handling. But test both on 10 real diffs from your target repo and compare.

**Add to spec:** A/B test plan. Run both models in parallel for a day, human-judge output quality.

### Trigger Scope (Open Question #2)

**Suggestion:** Start with PRs only. Direct pushes to main are usually hotfixes or automated commits—reviewing them creates noise without preventing issues. PRs are where you want the gate.

Exception: Add a `--full-review` flag for manual runs on commits before PR (local dev feedback).

### Access Pattern (Open Question #3)

**Critical:** Document this clearly. If GX-10 has no outbound, you'll need:
- Pre-downloaded models (obvious)
- Cached git clones (no `git fetch` from origin)
- Local git mirrors or manual sync

If you want "auto-pull on webhook," you need outbound. Decide now.

### Notification Strategy (Open Question #4)

**My preference:** File reports + digest mode.
- Every review → file
- CRITICAL findings → immediate chat
- Daily digest of WARN/INFO findings

Immediate chat for everything = notification fatigue.

### First Repo (Open Question #5)

**Agree** with `mesh-memory` or `openclaw`. Pick one with:
- Active development (daily commits)
- Mixed Rust/Python (tests your multi-language setup)
- Someone who will actually read the reports (Ray?)

`openclaw` might be better since you (Erik) can provide immediate feedback on report quality.

---

## Red Flags to Watch

1. **Prompt drift:** After a week of tuning, the prompt will be 3x longer. Document the base version that worked.

2. **Context window overflow:** 70B @ 32K context is generous, but large PRs + 3 context files might push it. Add chunking strategy (review file-by-file if diff > 10K tokens).

3. **Review latency:** If inference takes >2 minutes, the webhook will timeout or retry. Add async queue (Redis/SQLite) between webhook and agent.

4. **Security theater:** An agent that flags everything as WARN is worse than none. Track false positive rate religiously.

---

## Minor Typos/Nits

- "do_not_review" in agent profile has "Style nits (we have formatters)"—should this be "formatting nits"? Style and formatting are different.
- Appendix has placeholder "(TBD - need link from Woodhouse)" for agency templates—fill or remove before final
- "Hermes runtime" link is "https://github.com/[...]"—placeholder

---

## Summary

| Aspect | Rating | Notes |
|--------|--------|-------|
| Architecture | Good | Consider 2-3 agents vs 1 with 4 hats |
| Output format | Good | Add confidence + actionability fields |
| Workflow | Good | Add polling fallback, plan retention |
| Agency patterns | Missing | Add tool-use, reflection, memory |
| Scope | Right-sized | Tighten success criteria to metrics |
| Open questions | Clear | #3 (airgap) needs decision |

**Bottom line:** This will work. The biggest risk isn't technical—it's that the reviews become noise nobody reads. Guard against that with confidence scoring, reflection loops, and human feedback tracking from day one.

---

*Ready for Iteration 2 discussion once this runs for a week.*

# GX-10 Dev Pod - Iteration 1 Feedback

**Reviewer:** Ray  
**Date:** 2026-06-13  
**Status:** Candid technical review

---

## Overall Assessment

This is a solid foundation. The scope is appropriately constrained for a first iteration, and the problem statement is genuine—we do need persistent code review beyond what frontier APIs provide. However, there are several areas where reality will likely diverge from the plan, and some missing considerations that could derail or delay the project.

---

## Technical Feasibility

### ✅ Likely to Work

1. **Local 70B on 80GB VRAM** — Q4_K_M of Qwen3-72B or Llama 3.3 70B should fit comfortably (~40-45GB). llama.cpp is battle-tested for this use case.

2. **Structured output format** — The report template is well-designed and should be achievable with a well-crafted system prompt. JSON schema enforcement may be needed for reliability.

3. **Git webhook → local processing** — Standard pattern, plenty of prior art.

### ⚠️ Likely to Break / Need Rework

1. **llama.cpp HTTP server for this workload** — The server mode is designed for chat completions, not batch processing of code diffs. You may hit:
   - Context management issues (you need to keep file context + diff in memory)
   - Timeout issues on larger reviews
   - No native support for "review this multi-file diff" semantics
   
   **Suggestion:** Consider using the C++ API or a Python binding (llama-cpp-python) with a custom wrapper rather than raw HTTP. More control over batching and context windows.

2. **"32K context" assumption** — That's optimistic for reliable review. A large PR with 10+ files and full file context could easily exceed this. 
   
   **Suggestion:** Build a chunking strategy from day 1. Review file-by-file, aggregate findings.

3. **Systemd service with cron** — Cron is the wrong tool here. You need:
   - Webhook listener (long-running HTTP server)
   - Queue for async processing (commits can arrive faster than reviews complete)
   
   **Suggestion:** Use a proper queue (Redis, SQLite queue, or even just a thread pool) rather than cron. The architecture diagram shows "Review queue processor"—implement this properly.

---

## Missing Considerations

### Security
- **Model isolation:** Running a 70B model on the same host as your git repos? If the model is compromised (prompt injection → code execution), it has access to your codebase.
- **Webhook authentication:** GitHub webhooks need signature verification. Document this.
- **Secrets scanning:** Your reviewer should probably *not* be fed files containing API keys, even if it's local. Consider pre-filtering.

### Operational
- **Disk space for reports:** `~/gx10-reviews/{repo}/{date}/` will accumulate fast. What's the retention policy?  
  **Suggestion:** Add a cleanup job or size-based rotation from day 1.

- **Model download/update story:** 70B models are ~40GB. If you switch models or update quantization, how does the system handle this? Document the model path configuration.

- **Failure modes:** What happens when:
  - llama.cpp server is down? (Queue and retry? Drop?)
  - Review takes >5 minutes? (GitHub webhook timeout is 10s for async, 30s for sync)
  - VRAM is exhausted by another process?

### Development Experience
- **Local testing:** How do you test the reviewer without pushing commits? Need a CLI mode: `cat diff.patch | dev-pod-review --repo=mesh-memory`
- **Prompt iteration:** Changing the system prompt means restarting the llama.cpp server (context caching). This will slow iteration. Consider prompt templating that hot-reloads.

---

## Open Questions - My Take

### 1. Model Choice
**Recommendation:** Start with **Qwen3-72B**. Rationale:
- Stronger coding benchmarks on HumanEval/MBPP
- Better instruction following (critical for structured output)
- Supports function calling if you later want tool use
- Slightly smaller than Llama 3.3 70B (better VRAM headroom)

**Alternative:** If Qwen3 doesn't quantize well to Q4_K_M, fallback to Llama 3.3 70B.

### 2. Trigger Scope
**Recommendation:** Start with **PRs only**, not every commit.
- Reduces noise significantly
- Natural async boundary (PRs expect delayed feedback)
- Easier to handle via webhook (single event type)
- Direct pushes are often hotfixes or merges—you can add commit-level later

**Implementation:** Use `pull_request` webhook events, fetch the PR diff via GitHub API.

### 3. Notification Strategy
**Recommendation:** Start with **report files only**, add chat notifications later.
- Files are inspectable, diffable, grep-able
- Chat notifications risk alert fatigue
- When you add chat, do it only for CRITICAL + new categories (e.g., "new dependency with known CVE")

**One exception:** Post a summary to Telegram when the first review completes—good morale boost and proof of life.

### 4. First Repo
**Recommendation:** `mesh-memory`
- Rationale: Known codebase, Rust (static types help the model), active development
- Avoid `openclaw` initially—too much infrastructure surface area, hard to isolate failures

---

## Suggested Scope Adjustments

### Add to Iteration 1 (Critical)
1. **CLI testing mode** — Must be able to run reviews locally without webhooks
2. **Queue system** — SQLite-based or in-memory with persistence. Don't rely on cron.
3. **File-based config** — YAML or TOML for repo list, model path, webhook secret
4. **Basic auth/verification** — Webhook signature validation

### Move to Iteration 2 (Out of scope for now)
1. Chat notifications (keep CRITICAL logging only)
2. Multi-repo support (start with one)
3. Custom specialization loading (start with hardcoded reviewer profile)
4. Review history / trend analysis

### Consider Dropping
1. **"Learn patterns over time"** — This is mentioned in the problem statement but not in Iteration 1 goals. Good—keep it aspirational but don't implement. RAG over past reviews is a whole project.

---

## Implementation Suggestions

### Revised Architecture

```
┌─────────────────────────────────────────┐
│           GX-10 (192.168.1.100)         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │     Webhook Listener (FastAPI)   │   │
│  │     - Receives GitHub events      │   │
│  │     - Validates signatures        │   │
│  │     - Enqueues to SQLite          │   │
│  └─────────────┬─────────────────┘   │
│                │                      │
│  ┌─────────────▼─────────────────┐   │
│  │     Worker Pool (2-4 threads)  │   │
│  │  - Dequeues jobs                │   │
│  │  - Fetches diffs via GitHub API │   │
│  │  - Calls llama.cpp via Python   │   │
│  │  - Writes reports               │   │
│  └─────────────┬─────────────────┘   │
│                │                      │
│  ┌─────────────▼─────────────────┐   │
│  │     llama.cpp (local server)     │   │
│  │     - Single model, 1 concurrent │   │
│  └───────────────────────────────┘   │
└───────────────────────────────────────┘
```

### Tech Stack Recommendation

| Component | Suggestion | Why |
|-----------|------------|-----|
| Webhook server | FastAPI or Flask | Python ecosystem, easy validation |
| Queue | SQLite + `sqlite-queue` or Redis | Simple, persists across restarts |
| LLM client | `llama-cpp-python` | Better control than HTTP, streaming |
| Config | Pydantic + YAML | Validation + hot-reload friendly |
| Deployment | Systemd for webhook+worker, separate for llama.cpp | Isolate crashes |

### Day 1-2 Revised Checklist

1. [ ] Install llama-cpp-python on GX-10
2. [ ] Download Qwen3-72B Q4_K_M GGUF
3. [ ] Write minimal Python script: `review_diff.py diff.patch` → `review_output.md`
4. [ ] Test on real diff from mesh-memory
5. [ ] Verify VRAM usage and latency

Only then:
6. [ ] Add webhook listener
7. [ ] Add queue
8. [ ] Add GitHub API integration

---

## Red Flags to Watch For

1. **Review latency** — If a simple 3-file PR takes >2 minutes, the UX will degrade fast. Target <30s for typical reviews.

2. **Hallucinated findings** — 70B models still hallucinate. The "Suggested fix" section will be prone to this. Consider requiring a confidence threshold or marking suggestions as "AI-generated, verify before applying."

3. **Prompt brittleness** — Structured output from local models is less reliable than OpenAI/Anthropic APIs. Expect to iterate on the prompt heavily. Consider JSON mode + schema validation.

4. **GX-10 contention** — 48GB is already used. If another heavy workload starts, your reviews will fail mysteriously. Add VRAM monitoring/alerting.

---

## What I'd Do Differently

1. **Start with a simpler model** — Before the 70B, validate the pipeline with a 14B or 32B model. Faster iteration, easier to spot prompt issues. Upgrade to 70B once the system works.

2. **Pre-commit hook option** — For local dev, a pre-commit hook that calls the reviewer would catch issues before push. Harder to implement (needs local server), but valuable.

3. **Review the reviewer** — Log model outputs alongside diffs. After a week, sample 10 reviews and manually score them. Use this to tune the prompt.

4. **Consider vLLM instead of llama.cpp** — vLLM has better throughput for batch processing. llama.cpp is optimized for single-stream interactive. Worth benchmarking both.

---

## Final Verdict

**Scope:** ✅ Appropriately constrained for Iteration 1  
**Feasibility:** ⚠️ Doable, but expect 2-3x the estimated time  
**Risk Level:** Medium — the unknowns (prompt reliability, latency, queue behavior) are tractable but not trivial

**Biggest risk:** Prompt engineering for structured output on local 70B models. Budget extra time for this.

**Biggest opportunity:** If it works, this becomes the template for other specialized agency pods (docs, tests, security). Nail the architecture here.

---

## Questions for Erik

1. What's the actual 48GB already in use on GX-10? Is it safe to allocate 70GB to this, or should we reserve more headroom?
2. Do you have a preference between FastAPI/Flask, or is Python fine for the webhook server?
3. Are you open to starting with a 32B model for faster iteration, then upgrading?
4. For the first repo (mesh-memory), do you want to start with open PRs or wait for new ones?

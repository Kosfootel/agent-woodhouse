# GX-10 Dev Pod - Iteration 1 Spec (Consolidated)

**Status:** Draft - Post Ray + Liz Review  
**Author:** Erik  
**Contributors:** Ray, Liz  

---

## Problem Statement

We're building increasingly complex agent systems but lack dedicated code review, security auditing, and architectural oversight. Frontier models handle immediate tasks well but don't build long-term codebase understanding. We need a persistent, local "back of house" dev team that learns our patterns and continuously improves our products.

---

## Goals (Iteration 1)

1. **Deploy** a dedicated agency pod on GX-10 with clear specialization
2. **Establish** automated code review on every commit/PR
3. **Prove** value: catch at least one real issue or meaningful improvement in first week
4. **Measure** concrete metrics: inference latency, cost per review, false positive rate, human acceptance rate

**Non-Goals (this iteration):**
- Auto-apply fixes (suggest only)
- PR comments/integrations (file reports only)
- Multi-repo support (single repo pilot)
- Chat notifications beyond CRITICAL findings

---

## Technical Design

### Resource Allocation (GX-10)

| Resource | Available | Proposed Use |
|----------|-----------|--------------|
| VRAM | ~80GB free (128GB - 48GB used) | 70B model @ Q4_K_M (~40GB) + headroom |
| Model | TBD | **Qwen3-72B** (primary), Llama 3.3 70B (fallback) |
| Context | ~32K tokens | Full files + diffs + history |
| Runtime | Continuous | Systemd service with queue-based workers |

**Decision:** Start with Qwen3-72B for stronger coding benchmarks. Fallback to Llama 3.3 if quantization issues.

### Architecture (Revised)

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
         │
         │ (git webhook)
         ▼
┌─────────────────┐
│  GitHub Repos   │
│  (PRs only)     │
└─────────────────┘
```

**Key Changes from v1:**
- SQLite queue instead of cron (Ray)
- FastAPI webhook listener with signature validation (Ray)
- Python bindings (`llama-cpp-python`) vs HTTP server for better control (Ray)

### Agent Architecture (Revised - Multi-Agent)

**Decision:** Split into 3 lightweight sub-agents (Liz) rather than one with 4 specializations.

```yaml
agents:
  security_auditor:
    blocking: true
    focus: "Memory safety, unsafe blocks, crypto usage, auth flows"
    severity_threshold: CRITICAL
    
  pattern_reviewer:
    blocking: false
    focus: "Idioms, type hints, error handling, async correctness"
    severity_threshold: WARN
    
  architecture_steward:
    blocking: false
    focus: "Module boundaries, dependency direction, coupling, imports"
    severity_threshold: INFO
```

Each agent:
- Gets the same diff + relevant context files
- Produces findings with confidence + actionability scoring
- Runs reflection loop to self-critique before output
- Stores findings to shared `patterns.jsonl` for memory accumulation

### Report Format (Revised)

```markdown
# Review: repo-name @ abc1234

## Summary
- Files reviewed: 3
- Lines changed: 147
- Findings: 2 WARN, 1 INFO, 1 CRITICAL
- Latency: 23s
- Model: qwen3-72b-q4_k_m

## Critical
### C1: Potential SQL injection vector
**Agent:** security_auditor  
**Confidence:** high  
**Actionability:** auto-fixable  
**File:** `src/db/queries.rs:45`  
**Issue:** String interpolation in SQL query  
**Suggested fix:** Use parameterized queries  
**Context:** User input from `request.body.username` flows here  
**Rationale:** Untrusted input directly concatenated into query string

## Warnings
### W1: Unwrap in async context
**Agent:** pattern_reviewer  
**Confidence:** high  
**Actionability:** auto-fixable  
**File:** `src/mesh/sync.rs:89`  
**Issue:** `result.unwrap()` can panic, use `?` or match  
**Suggested fix:** Replace with `result?`  
**Context:** Previous commit showed this path is hit during recovery  
**Rationale:** Async contexts should propagate errors, not panic

## Info
### I1: New dependency introduced
**Agent:** security_auditor  
**Confidence:** high  
**Actionability:** discussion  
**Crate:** `base64 0.22`  
**Note:** Already used elsewhere, no action needed

## Negative Findings (what was checked and not found)
- Security: No hardcoded secrets detected
- Architecture: No circular dependencies introduced
- Patterns: All async functions properly propagate errors

## Agent Notes
- security_auditor: 3 findings, 2 auto-fixable
- pattern_reviewer: 1 finding, medium confidence
- architecture_steward: No concerns, import graph clean
```

**Key additions from Liz:**
- `confidence: high|medium|low` per finding
- `actionability: auto-fixable|suggested|discussion`
- `rationale` field forcing justification
- **Negative findings** section (builds trust)
- **Agent Notes** section (meta-summary)

---

## Implementation Plan (Revised Timeline)

**Ray:** Expect 2-3x the original Day 1-7 timeline due to prompt engineering complexity.

### Phase 1: Bootstrap (Day 1-3)
- [ ] Install `llama-cpp-python` on GX-10
- [ ] Download Qwen3-72B Q4_K_M GGUF
- [ ] Write minimal CLI: `python review_diff.py diff.patch --repo=mesh-memory`
- [ ] Test on real diff, verify VRAM usage and latency
- [ ] **Target:** <30s for typical 3-file PR

### Phase 2: Multi-Agent + Tooling (Day 4-6)
- [ ] Implement 3-agent split (security, patterns, architecture)
- [ ] Add reflection loop (self-critique pass)
- [ ] Add tool-use: `read_file`, `search_codebase`, `query_git_history`
- [ ] Test chunking strategy for large PRs (>10K tokens)

### Phase 3: Git Integration (Day 7-10)
- [ ] FastAPI webhook listener with signature validation
- [ ] SQLite queue for async processing
- [ ] Worker pool (2-4 threads)
- [ ] GitHub API integration for PR diffs

### Phase 4: Validation (Day 11-14)
- [ ] Run for 7 days on mesh-memory repo
- [ ] Track metrics: latency, false positive rate, human acceptance
- [ ] Manual sample: score 10 reviews for quality
- [ ] Draft Iteration 2 spec with learnings

---

## Security & Operational Considerations

### Security (Ray)
- **Webhook authentication:** GitHub signature verification required
- **Model isolation:** 70B model has git repo access—consider implications
- **Secrets scanning:** Pre-filter files containing API keys from model input

### Operational (Ray + Liz)
- **Report retention:** Rotate reports after 30 days or archive to cold storage
- **Model updates:** Document 40GB download/update story
- **Failure modes:**
  - llama.cpp down → Queue and retry with exponential backoff
  - Review >5min → Async processing (webhook returns immediately)
  - VRAM exhausted → Queue pause + alert
- **GX-10 contention:** Add VRAM monitoring; alert if available <20GB

---

## Open Questions - Decisions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Model choice | **Qwen3-72B** | Stronger coding benchmarks (Ray) |
| 2 | Trigger scope | **PRs only** | Reduces noise, natural async boundary (Ray + Liz) |
| 3 | Access pattern | **Outbound internet available** | Model download, git fetch, webhooks all enabled |
| 4 | Notifications | **Files + CRITICAL chat only** | Avoid notification fatigue (Liz) |
| 5 | First repo | **mesh-memory** | Known codebase, Rust, active dev (Ray + Liz agree) |

---

## Success Criteria

- [ ] Agent runs continuously on GX-10 for 7 days without manual intervention
- [ ] Reviews triggered automatically on PRs
- [ ] At least 1 meaningful finding (security, performance, or architecture) caught
- [ ] Average review latency <30s for typical 3-file PR
- [ ] False positive rate tracked and <30% (measured via manual sampling)
- [ ] Ray and Liz have reviewed this spec and provided feedback ✅
- [ ] Iteration 2 spec drafted with scaling plan

---

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| LLM Runtime | `llama-cpp-python` | Better control than HTTP (Ray) |
| Webhook Server | FastAPI | Python ecosystem, easy validation (Ray) |
| Queue | SQLite + `sqlite-queue` | Simple, persists across restarts (Ray) |
| Config | Pydantic + YAML | Validation + hot-reload friendly (Ray) |
| Deployment | Systemd | Separate services for webhook/worker vs llama.cpp |

---

## Red Flags to Watch (Ray + Liz)

1. **Review latency** — Target <30s. If >2min, UX degrades fast.
2. **Hallucinated findings** — Confidence scoring + reflection loop mitigate.
3. **Prompt brittleness** — Structured output from local models is harder than APIs. Budget extra iteration time.
4. **Notification fatigue** — Start minimal; add only when valuable.
5. **Context overflow** — Large PRs need chunking strategy from day 1.

---

## Appendix: Resources

- GX-10: 192.168.1.100, Ubuntu, 128GB VRAM (48GB used)
- llama-cpp-python: https://github.com/abetlen/llama-cpp-python
- Qwen3 GGUFs: https://huggingface.co/[...]
- Agency templates: (TBD - need link from Woodhouse)

---

## Feedback Summary

**Ray's contribution:**
- Queue-based architecture (not cron)
- CLI testing mode requirement
- Security considerations (webhook auth, secrets filtering)
- Timeline realism (2-3x original estimate)
- Model recommendation (Qwen3)

**Liz's contribution:**
- Multi-agent split (3 agents vs 1 with 4 hats)
- Confidence + actionability scoring in output
- Negative findings section
- Tool-use loop (read_file, search_codebase)
- Reflection loop for false positive reduction
- Memory accumulation via patterns.jsonl
- Polling fallback alongside webhooks

**Key tensions resolved:**
- Single vs multi-agent: → Multi-agent for focused expertise
- Every commit vs PRs only: → PRs only for Iteration 1
- File reports vs PR comments: → Files only, defer PR integration
- 70B immediately vs smaller first: → 70B but validate with CLI first

---

*Ready for Erik's final review and airgap decision before implementation.*

# GX-10 Dev Pod - Iteration 1 Spec

**Status:** Draft  
**Author:** Erik & Liz  
**Next:** Review by Ray + Liz  

---

## Problem Statement

We're building increasingly complex agent systems but lack dedicated code review, security auditing, and architectural oversight. Frontier models handle immediate tasks well but don't build long-term codebase understanding. We need a persistent, local "back of house" dev team that learns our patterns and continuously improves our products.

---

## Goals (Iteration 1)

1. **Deploy** a dedicated agency pod on GX-10 with clear specialization
2. **Establish** automated code review on every commit/PR
3. **Prove** value: catch at least one real issue or meaningful improvement in first week
4. **Document** learnings for Iteration 2 scaling

**Non-Goals (this iteration):**
- Auto-apply fixes (suggest only)
- Multi-agent specialization (single reviewer)
- External integrations beyond git

---

## Technical Design

### Resource Allocation (GX-10)

| Resource | Available | Proposed Use |
|----------|-----------|--------------|
| VRAM | ~80GB free (128GB - 48GB used) | 70B model @ Q4_K_M (~40GB) + headroom |
| Model | TBD | Qwen3-72B or Llama 3.3 70B via llama.cpp |
| Context | ~32K tokens | Full files + diffs + history |
| Runtime | Continuous | Systemd service with cron triggers |

### Architecture

```
┌─────────────────────────────────────────┐
│           GX-10 (192.168.1.100)         │
│  ┌─────────────────────────────────┐    │
│  │     llama.cpp server            │    │
│  │     (port 8081, 70B model)      │    │
│  └─────────────┬─────────────────┘    │
│                │                        │
│  ┌─────────────▼─────────────────┐     │
│  │     Dev Pod Agent             │     │
│  │  - Hermes runtime             │     │
│  │  - Agency templates           │     │
│  │  - Git webhook listener       │     │
│  │  - Review queue processor     │     │
│  └─────────────┬─────────────────┘     │
│                │                        │
│  ┌─────────────▼─────────────────┐     │
│  │     Review Reports            │     │
│  │  ~/gx10-reviews/{repo}/{date}/ │    │
│  └───────────────────────────────┘     │
└─────────────────────────────────────────┘
         │
         │ (git webhook)
         ▼
┌─────────────────┐
│  GitHub/GitLab  │
│  repos          │
└─────────────────┘
```

### Agent Profile

```yaml
name: "GX-10 Code Reviewer"
personality: "Thorough, security-conscious, pragmatic"
specializations:
  - rust_security: "Memory safety, unsafe blocks, crypto usage"
  - python_patterns: "Type hints, error handling, async correctness"
  - architecture: "Module boundaries, dependency direction, coupling"
  - performance: "Obvious bottlenecks, unnecessary clones/allocs"

do_not_review:
  - "Style nits (we have formatters)"
  - "Test coverage % (out of scope)"
  - "Documentation completeness (flag only, don't block)"

output_format: "structured markdown with severity: INFO/WARN/CRITICAL"
```

---

## Workflow

### Trigger: On Every Push

1. Webhook fires from GitHub → GX-10 (ngrok or local tunnel)
2. Agent fetches commit diff + relevant context files
3. Runs review against specializations
4. Writes report to `~/gx10-reviews/{repo}/{timestamp}-{commit-sha}.md`
5. (Optional) Posts summary to Telegram/Slack if CRITICAL findings

### Report Structure

```markdown
# Review: repo-name @ abc1234

## Summary
- Files reviewed: 3
- Lines changed: 147
- Findings: 2 WARN, 1 INFO

## Critical
*None*

## Warnings
### W1: Unwrap in async context
**File:** `src/mesh/sync.rs:89`  
**Issue:** `result.unwrap()` can panic, use `?` or match  
**Suggested fix:** Replace with `result?`  
**Context:** Previous commit showed this path is hit during recovery

## Info
### I1: New dependency introduced
**Crate:** `base64 0.22`  
**Note:** Already used elsewhere, no action needed

## Architectural Notes
- New module `mesh/relay.rs` follows existing patterns ✅
- Consider extracting retry logic into shared util (opportunity)
```

---

## Implementation Plan

### Phase 1: Bootstrap (Day 1-2)
- [ ] Deploy llama.cpp server on GX-10 port 8081
- [ ] Download Qwen3-72B or Llama 3.3 70B
- [ ] Verify VRAM usage and inference speed
- [ ] Create systemd service for auto-start

### Phase 2: Agent Setup (Day 2-3)
- [ ] Install Hermes runtime on GX-10
- [ ] Configure agency templates for code reviewer
- [ ] Test manual review on sample diff
- [ ] Tune prompt for structured output

### Phase 3: Git Integration (Day 3-4)
- [ ] Set up webhook endpoint (Python/Node listener)
- [ ] Clone one test repo (pick something active)
- [ ] Wire webhook → agent → report
- [ ] Test end-to-end on real commit

### Phase 4: Validation (Day 5-7)
- [ ] Run for 1 week on primary repo
- [ ] Collect findings, tune false positives
- [ ] Document what worked / what didn't
- [ ] Draft Iteration 2 spec

---

## Open Questions

1. **Model choice:** Qwen3-72B vs Llama 3.3 70B vs something else? Qwen3 has strong coding scores but Llama may be more familiar.

2. **Trigger scope:** All commits or just PRs? PRs only reduces noise but misses direct pushes.

3. **Access pattern:** Does GX-10 need outbound internet for model download, or are we air-gapping?

4. **Notification strategy:** Report files only, or push to chat for CRITICAL findings?

5. **First repo:** Which codebase do we target? Suggest `mesh-memory` or `openclaw` since we know them.

---

## Success Criteria

- [ ] Agent runs continuously on GX-10 for 7 days without manual intervention
- [ ] Reviews triggered automatically on commits
- [ ] At least 1 meaningful finding (security, performance, or architecture) caught
- [ ] Ray and Liz have reviewed this spec and provided feedback
- [ ] Iteration 2 spec drafted with scaling plan

---

## Appendix: Resources

- GX-10: 192.168.1.100, Ubuntu, 128GB VRAM (48GB used)
- Hermes: https://github.com/[...]
- llama.cpp: https://github.com/ggerganov/llama.cpp
- Agency templates: (TBD - need link from Woodhouse)

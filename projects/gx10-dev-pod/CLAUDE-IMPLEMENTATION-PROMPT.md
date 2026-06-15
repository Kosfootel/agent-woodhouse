# Claude Implementation Prompt: GX-10 Dev Pod Phase 1

**Context:** This is a task to implement a local AI-powered code review system on a GPU server. You are the implementation agent.

**Your Role:** Infrastructure engineer + ML ops. Build the foundation that later phases will extend.

---

## Task

Implement **Phase 1: Bootstrap** of the GX-10 Dev Pod specification. This establishes the core review capability before adding multi-agent complexity or git integration.

**Full spec:** `/Users/FOS_Erik/.openclaw/workspace/projects/gx10-dev-pod/ITERATION-1-SPEC-CONSOLIDATED.md`

---

## Deliverables (Phase 1)

### 1. LLM Runtime Setup (GX-10: 192.168.1.100)

**Requirements:**
- [ ] SSH into GX-10 and assess current state (VRAM usage, available space)
- [ ] Install `llama-cpp-python` with CUDA support
- [ ] Download Qwen3-72B Q4_K_M GGUF (~40GB)
  - HuggingFace: https://huggingface.co/[...] (use GGUF versions)
  - Alternative: https://huggingface.co/bartowski/Qwen3-72B-GGUF
- [ ] Verify model loads and responds to basic prompts
- [ ] Document VRAM usage at load and during inference

**Acceptance:** `python -c "from llama_cpp import Llama; print('OK')"` works

---

### 2. CLI Review Tool (`review_diff.py`)

**Requirements:**
- [ ] Create Python CLI at `/opt/gx10-dev-pod/review_diff.py`
- [ ] Input: diff file path + repo name
- [ ] Output: structured markdown report to stdout
- [ ] System prompt implements single-agent reviewer with:
  - Focus areas: security (blocking), patterns (warn), architecture (info)
  - Severity tiers: INFO/WARN/CRITICAL
  - Confidence scoring: high/medium/low
  - Actionability: auto-fixable/suggested/discussion
  - Rationale field for each finding
  - Negative findings section
- [ ] Include reflection loop: self-critique before final output
- [ ] Add timing: report latency in output

**Example usage:**
```bash
cat pr.diff | python review_diff.py --repo=mesh-memory > report.md
```

**Acceptance:** Successfully reviews a real diff from mesh-memory repo

---

### 3. Validation & Benchmarking

**Requirements:**
- [ ] Clone mesh-memory repo (if not present)
- [ ] Extract a real recent PR diff (3-5 files changed)
- [ ] Run review, capture:
  - Total latency (target: <30s for 3-file PR)
  - VRAM usage during inference
  - Token throughput (tokens/sec)
  - Output quality assessment
- [ ] Test edge cases:
  - Large diff (>10K tokens) - verify chunking or graceful handling
  - Binary files - skip gracefully
  - Empty diff - handle gracefully

**Acceptance:** 
- [ ] At least one meaningful finding generated
- [ ] Latency <30s for typical case
- [ ] No crashes on edge cases

---

### 4. Documentation

**Requirements:**
- [ ] Create `/opt/gx10-dev-pod/README.md` with:
  - Installation steps
  - Usage examples
  - Configuration options (YAML or CLI flags)
  - Troubleshooting section
- [ ] Document prompt engineering decisions made
- [ ] Note any deviations from spec with rationale

---

## Technical Stack

| Component | Expected |
|-----------|----------|
| LLM Runtime | `llama-cpp-python` with CUDA |
| Model | Qwen3-72B Q4_K_M GGUF |
| Language | Python 3.10+ |
| Config | Pydantic + YAML |
| Target | <30s latency for 3-file review |

---

## Environment Details

- **Host:** GX-10 at 192.168.1.100
- **OS:** Ubuntu (confirm version)
- **GPU:** 128GB VRAM (48GB currently used)
- **Outbound internet:** ✅ Available
- **Storage:** Verify sufficient space for 40GB model

---

## Constraints

1. **Single agent for Phase 1** - Multi-agent split comes in Phase 2
2. **No git/webhooks yet** - CLI only, files as input
3. **No tool-use yet** - Reflection loop only, no file reading/searching
4. **Suggest only** - Never auto-modify code
5. **File reports only** - No chat integrations

---

## Definition of Done

Phase 1 is complete when:
- [ ] All deliverables above are met
- [ ] README.md documents how to run a review
- [ ] Erik can SSH to GX-10 and run: `python review_diff.py --help`
- [ ] Sample report from mesh-memory diff is saved to `/opt/gx10-dev-pod/sample-report.md`

---

## Suggestions for Improvement

After completing the implementation, analyze this prompt and suggest:
1. What was unclear or could be better specified
2. Technical decisions you'd make differently
3. Phase 2 preparation notes
4. Any risks or blockers discovered

---

**Questions?** Ask Erik or Liz for clarification on spec details.

**Success criteria:** Working CLI that generates structured code reviews in <30s on GX-10.

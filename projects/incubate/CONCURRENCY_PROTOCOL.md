# Concurrency & Resource Protocol
*Filed: 2026-04-01 | Author: Woodhouse | Status: ACTIVE*

This document governs how the three-agent mesh manages shared Anthropic token budget, Ollama local inference, sub-agent concurrency, and heartbeat scheduling.

---

## 1. Heartbeat Stagger

To prevent simultaneous API calls and context interference, heartbeats are offset by agent:

| Agent | Offset |
|-------|--------|
| Woodhouse | :00 (on the hour) |
| Ray | :10 |
| Liz | :20 |

- All heartbeats run at 1-hour intervals anchored to the above offsets
- Liz anchored via restart cron at 13:20 EDT 2026-04-01; subsequent beats self-perpetuate from there
- If any agent restarts its gateway, it should attempt to re-anchor to its offset slot

---

## 2. Local Inference (Ollama)

Ollama is available and active on **Liz's node** (192.168.50.23):

- **Current model:** glm-4.7-flash (19GB)
- **RAM headroom:** ~23GB available; practical ceiling ~20GB safe (iGPU shares pool)
- **Heartbeats offloaded to local Ollama** — no Anthropic burn on routine checks
- Additional models viable: `qwen2.5:14b`, `llama3.1:8b`, `mistral-nemo:12b`
- Ray and Woodhouse: Ollama not confirmed available — use Anthropic unless local inference verified

**Routing preference:** Route heartbeats, light classification, and summarisation tasks to Ollama where available. Reserve Anthropic capacity for reasoning-heavy work.

---

## 3. Sub-Agent Serialisation

- **Liz:** maxConcurrent = 4 (subagents: 8). Default posture: **serialise** coding sub-agents unless the task explicitly requires parallelism AND it is low-Anthropic-impact.
- **Woodhouse / Ray:** Same principle — prefer sequential spawns on non-urgent workloads.
- **Parallelism permitted when:**
  - Explicitly time-critical
  - Sub-tasks are Ollama-routed or otherwise low-token-cost
  - Mr. Ross has explicitly requested parallel execution

---

## 4. Heavy Work Coordination

Before any agent commences substantial Anthropic load (large builds, multi-file codegen, extended research chains), it must:

1. Send an A2A heads-up to Woodhouse stating: scope of work, estimated token load (rough), and expected duration
2. Wait for Woodhouse acknowledgement before proceeding (or proceed after 2 minutes with no response, logging the attempt)
3. Woodhouse tracks aggregate load and may ask an agent to defer

"Substantial" = any task expected to consume >50K tokens or spawn >3 concurrent sub-agents.

---

## 5. Overload / Rate-Limit Protocol (529 Errors)

On receiving a 529 (overloaded) or rate-limit response from Anthropic:

1. **Do not** spawn parallel retry attempts
2. Wait **30–60 seconds** before first retry
3. If second attempt also fails: wait **2 minutes**, notify Woodhouse via A2A, and queue the task
4. Log all 529 occurrences in `memory/YYYY-MM-DD.md` for consumption tracking
5. Woodhouse aggregates and reports to Mr. Ross if pattern persists

---

## 6. Anthropic Budget — Standing Rules

*(As of 2026-03-28: limits upped, reload enabled — all three agents at full capacity)*

- No per-agent pacing restrictions currently active
- Woodhouse remains custodian — monitors for signs of approaching ceiling
- All agents report rate-limit errors to Woodhouse immediately
- Liz note: Codex sub-agent spins may not roll up in token counts — track workload in aggregate, not API calls alone

---

## Revision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-04-01 | Initial draft, post-consensus synthesis | Woodhouse |

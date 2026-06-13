# Multi-Agent Task Patterns Library

**Version:** 1.0  
**Date:** 2026-06-10  
**Status:** Active (Living Document)  
**Steward:** Woodhouse

---

## Overview

This library catalogs proven coordination patterns for the OpenClaw agent fleet. Each pattern includes:
- **When to use** and **when NOT to use**
- **Common failure modes** observed in practice
- **Recovery strategies** with specific OpenClaw primitives
- **Decision criteria** for choosing the right pattern

These patterns are derived from actual fleet operations, not theory. They reflect lessons learned from Vigil builds, agency agent delegation, Hermes retirement, and the A2A mesh.

---

## Pattern Catalog

### 1. FAN-OUT (Parallel Subagents)

**Description:** Spawn multiple independent subagents simultaneously to work on parallel tasks, then collect results.

**When to Use:**
- Multiple independent workstreams with no cross-dependencies
- Need to maximize throughput on parallelizable work
- Tasks have clear boundaries and isolated deliverables
- Examples from experience:
  - Vigil MVP: Backend Security Service + Frontend Dashboard + Infrastructure Setup running in parallel
  - Competitor research across multiple sources simultaneously
  - Device discovery across multiple network protocols

**When NOT to Use:**
- Tasks have sequential dependencies (use Pipeline instead)
- Shared state or resources require coordination
- Result synthesis requires real-time collaboration between workers
- Low task count where overhead exceeds benefit (use direct execution)

**OpenClaw Primitives:**
- `sessions_spawn` with `context: "fork"` for each parallel task
- `sessions_yield` to await completion (push-based, no polling)
- Auto-announcement of descendant results to parent

**Implementation Pattern:**
```
1. Define N independent tasks
2. Spawn all N subagents simultaneously
3. Use sessions_yield to wait for all completions
4. Collect results via auto-announcement
5. Synthesize/merge outputs in parent
```

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Partial timeout | One subagent exceeds time limit | Document partial success, spawn recovery agent for failed slice |
| Resource exhaustion | Too many concurrent subagents | Implement concurrency limits (max 3-5 parallel) |
| Context ceiling | Combined output exceeds limits | Stream results incrementally, use files for large outputs |
| Stale coordination | Parent restarts while children run | Use TaskFlow for durable orchestration |

**Recovery Strategy:**
- For partial failures: Identify which subagent failed, spawn recovery task with narrowed scope
- For full failure: Retry with reduced parallelism or sequential fallback
- Document subagent status in parent session (e.g., "ILHCEVR investigation #2: Timed out (data loading)")

**Decision Checklist:**
- [ ] Tasks have no inter-dependencies?
- [ ] Results can be merged post-hoc?
- [ ] Total expected output < 50K tokens?
- [ ] Parent has capacity to manage N children?

---

### 2. PIPELINE (Sequential Handoffs)

**Description:** Chain subagents where each stage's output becomes the next stage's input.

**When to Use:**
- Work naturally decomposes into sequential phases
- Each phase requires different expertise/models
- Quality gates needed between stages
- Examples from experience:
  - Design → Implementation → Testing → Deployment
  - Research → Analysis → Synthesis → Documentation
  - Data extraction → Transformation → Validation → Loading

**When NOT to Use:**
- Stages can run in parallel (use Fan-Out)
- Handoff overhead exceeds work time (use single agent)
- Tight feedback loops needed between stages

**OpenClaw Primitives:**
- `sessions_spawn` with explicit context passing
- `sessions_yield` between stages
- File-based state for large handoffs
- TaskFlow for durable pipeline state

**Implementation Pattern:**
```
1. Stage 1: Spawn subagent with input context
2. sessions_yield for completion
3. Extract/validate Stage 1 output
4. Stage 2: Spawn subagent with Stage 1 output as context
5. Repeat until final stage
6. Final validation and completion
```

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Handoff corruption | Output format drift | Enforce JSON Schema contracts between stages |
| Cascading failure | Early stage produces invalid output | Gate validation before advancing to next stage |
| Stage timeout | Individual stage exceeds limit | Parallel checkpointing, resumable stages |
| Context loss | Parent restart loses pipeline state | Use TaskFlow `createManaged` + `stateJson` |

**Recovery Strategy:**
- Implement validation gates between stages
- Allow stage retry (max 3 attempts per Orchestrator pattern)
- Store intermediate outputs to files for recovery
- Use TaskFlow revisions for conflict-safe mutations

**Quality Gate Enforcement:**
```
- Evidence required: All decisions based on actual agent outputs
- Retry limits: Maximum 3 attempts per task before escalation
- Clear handoffs: Each agent gets complete context and specific instructions
```

---

### 3. VOTING / CONSENSUS (Multiple Agents Same Task)

**Description:** Assign identical or variant tasks to multiple agents, then aggregate results for consensus or diversity.

**When to Use:**
- High-stakes decisions requiring confidence validation
- Creative tasks benefiting from multiple perspectives
- Critical code requiring review redundancy
- Unclear optimal approach, want to explore solution space

**When NOT to Use:**
- Deterministic tasks with clear correct answer (wasteful)
- Tight time constraints (multiplies latency)
- Limited context budget

**OpenClaw Primitives:**
- Multiple `sessions_spawn` with same or variant prompts
- Result aggregation in parent
- Optional: Different models for each voter

**Implementation Pattern:**
```
1. Define task with clear output format
2. Spawn 3-5 agents with same or variant prompts
3. Collect all outputs
4. Compare/analyze for consensus or divergence
5. Select or synthesize final answer
6. Document confidence level and dissent
```

**Variants:**
- **Unanimous:** All must agree (strict consensus)
- **Majority:** Simple majority wins
- **Diversity:** Collect different approaches, synthesize best elements
- **Model Mix:** Different models (kimi, nemotron) for perspective variety

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Split consensus | Genuine disagreement | Escalate to human or expand search space |
| Groupthink | Agents converge on wrong answer | Use diverse models/prompts |
| Format drift | Different output structures | Enforce strict JSON Schema |
| Timeout variance | One agent much slower | Set aggressive timeouts, use partial results |

---

### 4. MONITOR / DELEGATE (Parent Watches Children)

**Description:** Parent agent spawns subagents and actively monitors their progress, intervening on failure or timeout.

**When to Use:**
- Long-running subagent tasks requiring oversight
- Need to respond to partial failures without full restart
- Tasks have checkpoints where parent decisions needed
- Subagent autonomy with escalation paths

**When NOT to Use:**
- Simple fire-and-forget tasks (use direct spawn)
- Parent cannot maintain session (use TaskFlow for durability)

**OpenClaw Primitives:**
- `sessions_spawn` for subagent creation
- `sessions_yield` with timeout awareness
- `process(action: "poll")` for status checks when needed
- TaskFlow for durable monitoring state

**Implementation Pattern:**
```
1. Spawn subagent with clear deliverables and checkpoint milestones
2. Monitor via sessions_yield or periodic poll
3. On checkpoint: Evaluate progress, decide continue/escalate/abort
4. On failure: Spawn recovery agent with narrowed scope
5. On success: Collect results, validate, complete
```

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Silent failure | Subagent hangs without error | Implement heartbeat/checkpoints |
| Zombie subagent | Subagent orphaned on parent restart | TaskFlow parent linkage |
| Monitor overhead | Parent spends all time polling | Use push-based sessions_yield |
| Escalation fatigue | Too many recoveries needed | Set hard limits, escalate to human |

**Recovery Strategy:**
- Document subagent status clearly: "ILHCEVR investigation #1: Completed (502 fix)", "ILHCEVR investigation #2: Timed out (data loading)"
- Implement checkpoint-based monitoring
- Maintain retry counters to prevent infinite recovery loops
- Define clear escalation criteria

---

### 5. TASKFLOW ORCHESTRATION (Durable Multi-Step)

**Description:** Use TaskFlow for work that must survive session restarts and coordinate across multiple detached steps.

**When to Use:**
- Multi-step work spanning multiple prompts/sessions
- Work that waits on external systems or human replies
- Need persistent state across restarts
- Plugin/tool work requiring conflict-safe mutations
- Durable background jobs with one owner

**When NOT to Use:**
- Single-turn completions (overhead not justified)
- Fire-and-forget subagents (use sessions_spawn directly)
- Real-time coordination (TaskFlow has persistence overhead)

**OpenClaw Primitives:**
- `api.runtime.tasks.flow.fromToolContext(ctx)` or `bindSession()`
- `createManaged()` for orchestrated flows
- `runTask()` to link child tasks to flow
- `setWaiting()` / `resume()` for external waits
- `finish()` / `fail()` for completion
- `getTaskSummary()` for health monitoring

**Implementation Pattern:**
```
1. Create managed flow with goal and initial state
2. Run child task(s) via runTask()
3. Set waiting if blocked on external input
4. Resume when unblocked
5. Iterate until complete
6. Finish or fail with final state
```

**State Management:**
- `stateJson`: Persisted state bag between steps
- `currentStep`: Track pipeline phase
- `waitJson`: Structured wait metadata (e.g., reply channel, thread key)
- Revision tracking for conflict-safe mutations

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Revision conflict | Concurrent mutations | Automatic retry with latest revision |
| State bloat | Overly large stateJson | Store only minimum state, reference files |
| Lost waits | Wait condition cleared but not resumed | Implement idempotent resume |
| Orphaned tasks | Flow cancelled but children run | Use cancel() to propagate to linked children |

---

### 6. AGENCY AGENT SPECIALIZATION (Role-Based Delegation)

**Description:** Delegate to specialized agency agents with defined personas for specific task types.

**When to Use:**
- Task matches known agency agent specialty
- Need consistent expertise/persona across similar tasks
- Work benefits from specialized knowledge (security, UX, DevOps, etc.)

**When NOT to Use:**
- No matching agency agent exists
- Task requires generalist approach
- Context overhead of agent persona not justified

**OpenClaw Primitives:**
- Agency agent in `~/.openclaw/agency-agents/`
- `sessions_spawn` with agent-specific context
- Agent's SOUL.md and TOOLS.md for behavior

**Implementation Pattern:**
```
1. Identify task type from library (security-engineer, backend-architect, etc.)
2. Read agent's SKILL.md or AGENTS.md if needed
3. Spawn with task-specific context
4. Agent applies its persona and expertise
5. Collect specialized output
```

**Agency Agent Types Used:**
- `security-engineer`: Security endpoints, scanning, policy enforcement
- `backend-architect`: API design, database schemas, infrastructure
- `frontend-specialist`: UI components, dashboard, UX
- `orchestrator`: Pipeline management, quality gates, coordination
- `competitor-research`: Market analysis, competitive intelligence

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Agent mismatch | Task misunderstood scope | Clearer task definition, narrower scope |
| Context ceiling | Complex specs with file reads fail | nemotron returns reasoning content, may choke parser |
| Process death | Hermes/log shows "llm_call" then nothing | Systemd vs code crash, investigate root cause |
| Tool unavailability | Agent expects tool not present | Verify TOOLS.md for agent |

---

## Decision Criteria

### Subagent vs Direct Execution

| Factor | Subagent | Direct |
|--------|----------|--------|
| Task complexity | Complex, multi-step | Simple, single-action |
| Need for isolation | Yes (separate context) | No |
| Parallel execution | Required | Not needed |
| Different expertise | Different model/agent needed | Same model sufficient |
| Coordination overhead | Worth the benefit | Overhead exceeds value |
| Time sensitivity | Can tolerate yield latency | Immediate response needed |

**Rule of Thumb:**
- < 5 min of work: Direct execution
- 5-30 min, single thread: Direct or single subagent
- > 30 min, parallelizable, or requires oversight: Subagent pattern

### Sync vs Async

| Factor | Sync (sessions_yield) | Async (TaskFlow) |
|--------|----------------------|------------------|
| Session continuity | Parent can wait | Parent may restart |
| Human in loop | Real-time response | Wait for human reply |
| External dependencies | None | File system, APIs, humans |
| State persistence | Not needed | Required |
| Completion urgency | Immediate | Can resume later |

**Rule of Thumb:**
- Real-time coordination: Sync with sessions_yield
- Cross-session durability: TaskFlow with setWaiting/resume
- Fire-and-forget: Direct spawn without yield (if no result needed)

---

## Failure Taxonomy

### Common Failure Modes Across All Patterns

| Mode | Pattern | Root Cause | Mitigation |
|------|---------|------------|------------|
| Context overflow | All | Too much state/output | Stream to files, incremental delivery |
| Timeout exhaustion | Pipeline, Monitor | Task underestimated | Break into smaller tasks, checkpoint |
| Coordination lost | Fan-Out, Monitor | Parent restart | Use TaskFlow for durability |
| Stale context | Pipeline | Assumptions invalidated | Re-validate at each gate |
| Resource deadlock | Fan-Out | Shared resource contention | Explicit resource claims, timeouts |
| Format drift | Pipeline, Voting | Schema enforcement weak | JSON Schema validation between stages |
| Silent failure | Monitor | No heartbeat/checkpoint | Implement periodic status reports |

### Escalation Criteria

Escalate to human when:
1. Retry limit exceeded (3 attempts per pattern)
2. Consensus cannot be reached (Voting pattern)
3. Recovery agent also fails
4. TaskFlow in failed state with no clear recovery path
5. Pattern selection unclear (architectural decision needed)

---

## Template for Future Pattern Additions

```markdown
### N. PATTERN NAME

**Description:** One-line summary

**When to Use:**
- Scenario 1
- Scenario 2

**When NOT to Use:**
- Anti-pattern 1
- Anti-pattern 2

**OpenClaw Primitives:**
- List relevant primitives

**Implementation Pattern:**
Step-by-step workflow

**Failure Modes Observed:**
| Failure | Cause | Recovery |
|---------|-------|----------|
| Mode | Cause | Recovery |

**Recovery Strategy:**
Description of recovery approach

**Decision Criteria:**
- Checklist item 1
- Checklist item 2
```

---

## Related Resources

- **TaskFlow Skill:** `~/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/taskflow/SKILL.md`
- **TaskFlow Inbox Triage Example:** `~/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/taskflow-inbox-triage/SKILL.md`
- **Agency Agents:** `~/.openclaw/agency-agents/`
- **Fleet Topology:** `memory/briefs/fleet-topology.md` (if exists)

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-06-10 | 1.0 | Initial catalog based on Vigil builds, Hermes retirement, A2A mesh experience |

---

*This is a living document. Update with new patterns, failure modes, and recovery strategies as the fleet evolves.*

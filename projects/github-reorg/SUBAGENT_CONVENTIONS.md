# Subagent Conventions — GitHub Reorg Project

**Purpose:** Standard operating procedures for all subagents working on repository reorganization.

**Applies To:**
- Journal subagent (this agent)
- Project manager subagent
- GitHub migration subagents
- Code review subagents

---

## File Locations

| Resource | Path |
|----------|------|
| Journal entries | `~/.openclaw/workspace/projects/github-reorg/journal/YYYY-MM-DD-description.md` |
| Decision records (ADRs) | `~/.openclaw/workspace/projects/github-reorg/decisions/ADR-NNNN-description.md` |
| Change log | `~/.openclaw/workspace/projects/github-reorg/journal/CHANGELOG.md` |
| Task assignments | `~/.openclaw/workspace/projects/github-reorg/tasks/` |
| Deliverables | `~/.openclaw/workspace/projects/github-reorg/deliverables/` |

---

## Decision Recording (Required)

**Any** choice with downstream effects requires an ADR:
- Repository naming conventions
- Migration sequencing
- CI/CD configuration choices
- Permission/branch protection policies

**Process:**
1. Draft ADR using `decisions/ADR_TEMPLATE.md`
2. Number sequentially (ADR-0001, ADR-0002, etc.)
3. Filename: `ADR-NNNN-brief-description.md`
4. Update `CHANGELOG.md` with `[DECISION]` entry
5. Reference the ADR in all related task files

---

## Change Logging (Required)

Every completed task or significant action requires a CHANGELOG entry.

**Categories:** See CHANGELOG.md header for category definitions.

**Format:**
```markdown
### YYYY-MM-DD HH:MM EDT — [CATEGORY] Description

**Actor:** [Your subagent name]  
**Related ADR:** [If applicable]  
**Files Changed:** [List paths]  
**Repositories:** [If applicable]

Brief description of what was done.
```

---

## Repository Naming Standards

| Type | Pattern | Example |
|------|---------|---------|
| Agent-specific | `agent-{name}` | `agent-woodhouse`, `agent-ray`, `agent-liz` |
| Shared infrastructure | `agent-shared` | `Kosfootel/agent-shared` |
| Admin/personal | `erik-ross` | `Kosfootel/erik-ross` |
| Project repos | `projects/{name}` or existing | `Kosfootel/projects/incubate` |

---

## Before You Act

1. **Read first:** Check `journal/` and `decisions/` for relevant prior work
2. **Log your presence:** Add entry to CHANGELOG.md when you start
3. **Check for blockers:** Review open tasks in `tasks/` folder
4. **Record decisions:** If your work requires a choice, write an ADR

---

## When You Complete Work

1. Update `CHANGELOG.md` with `[RESOLVED]` or completion entry
2. Move deliverables to `deliverables/` folder
3. Mark tasks complete in `tasks/` (don't delete — append status)
4. Reference any ADRs used

---

## Communication

- **Report to:** Woodhouse (main session)
- **Format:** Concise summary + key details + next steps
- **No external actions:** Do not tweet, email, or post without explicit instruction

---

*Conventions version: 1.0*  
*Established: 2026-04-11*  
*Author: Journal Subagent (github-reorg-journal)*

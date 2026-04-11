# ADR-0001: Repository Naming and Merge Strategy

## Status
**Accepted** — 2026-04-11

## Context
Phase 1 audit revealed inconsistent naming across agent repositories. Need standardized naming convention for clarity and maintainability.

## Decision

### 1. Ray's Internal Repository Merge
**Decision:** Merge `BobbyRayBot-Internal` into `agent-ray`
**Constraint:** Non-destructive — no files or folders overwritten
**Approach:** 
- Audit both repos for file/folder conflicts before merge
- Rename conflicting files with `_internal` suffix if needed
- Preserve full history from both repositories

### 2. Woodhouse Rename
**Decision:** Rename `Woodhouse` → `agent-woodhouse` for consistency
**Rationale:** Standardizes `agent-{name}` convention across all agent repos
**Note:** Repository will remain public (content already appropriate)

### 3. Access Control Matrix
**Decision:** All agents have appropriate permissions on `agent-shared`
**Matrix:**
| Repository | Woodhouse | Ray | Liz | Erik |
|------------|-----------|-----|-----|------|
| agent-woodhouse | Admin | Read | Read | Admin |
| agent-ray | Read | Admin | Read | Admin |
| agent-liz | Read | Read | Admin | Admin |
| agent-shared | Write | Write | Write | Admin |

## Consequences
- **Positive:** Clear naming convention, easier navigation
- **Positive:** Consolidated Ray repositories reduce confusion
- **Negative:** GitHub redirects handle renames, but external references may break
- **Mitigation:** Update documentation and bookmarks post-rename

## Implementation
- See Phase 2 tasks in `tasks/backlog.md`

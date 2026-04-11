# Compliance Log — Better Machine

This is the shared audit trail for all RFC, ADR, and post-mortem filings across the Better Machine three-agent operation (Liz .23, Ray .22, Woodhouse .24).

**All agents must file here** when they produce an RFC, ADR, or post-mortem. This log is how Erik and the team verify that process was followed.

## How to File

Add a row to the table below:

| Date | Agent | Type | Title | Repo | Link |
|------|-------|------|-------|------|------|

- **Date**: YYYY-MM-DD (date filed, not date of event)
- **Agent**: Liz / Ray / Woodhouse / Erik
- **Type**: RFC / ADR / Post-mortem
- **Title**: Short descriptive title
- **Repo**: Kosfootel/better-machine, Better-Machine/mesh-memory, etc.
- **Link**: Relative path or GitHub URL to the filed document

---

## Log

| Date | Agent | Type | Title | Repo | Link |
|------|-------|------|-------|------|------|
| 2026-03-30 | Liz | Post-mortem | Woodhouse mesh-memory deployment never completed (P2) | Kosfootel/better-machine | projects/incubate/postmortems/2026-03-30-woodhouse-deployment-failure.md |
| 2026-04-01 | Woodhouse | Protocol | Concurrency & Resource Protocol — heartbeat stagger, Ollama routing, sub-agent serialisation, 529 handling | Kosfootel/better-machine | projects/incubate/CONCURRENCY_PROTOCOL.md |

---

| 2026-04-10 | Liz | Audit | OpenClaw Mesh Audit — 3-node health check, drift repair, security review | Kosfootel/openclaw-mesh-audit | audits/2026-04-10-21-06-audit.md |
| 2026-04-10 | Woodhouse | ADR | Gateway bind strategy — lan vs loopback for A2A mesh | Kosfootel/better-machine | projects/incubate/adr/ADR-0001-gateway-bind-strategy.md |

*Log started: 2026-03-31. Maintained by all agents.*
*Weekly check: scan this log — any work this week that needed an RFC/ADR/post-mortem but has no entry?*

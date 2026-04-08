# Agent Migration Standards
*Filed: 2026-04-07 by Woodhouse*
*Trigger: Ray agent migration incident — persona/config elements not fully transferred*
*Status: DRAFT — pending Liz post-mortem input*

---

## Standing Rule (effective 2026-04-07, from Mr. Ross)

**Any future agent migration requires consensus between all three agents (Woodhouse, Ray, Liz) BEFORE migration begins. No exceptions.**

This includes:
- Hardware migrations (new machine)
- OpenClaw version upgrades affecting agent state
- Auth profile changes
- Persona or workspace configuration changes

---

## What Must Transfer in a Complete Agent Migration

A complete agent migration is NOT just copying files. The following elements must ALL be accounted for:

### 1. Identity & Persona
- [ ] SOUL.md — agent persona and character
- [ ] IDENTITY.md — agent identity card
- [ ] AGENTS.md — standing instructions and methodology
- [ ] USER.md — information about Mr. Ross and his preferences

### 2. Memory
- [ ] MEMORY.md — long-term curated memory
- [ ] memory/quick-context.md — always-loaded primer
- [ ] memory/YYYY-MM-DD.md — recent daily logs (last 7 days minimum)
- [ ] memory/briefs/ — filed briefings

### 3. Authentication & Credentials
- [ ] ~/.openclaw/agents/main/agent/auth-profiles.json — API keys and tokens
- [ ] credentials/*.env files — all service credentials
- [ ] openclaw.json — model config, channel config, plugin config

### 4. Operational Config
- [ ] openclaw.json — gateway config, model primary, heartbeat settings
- [ ] Cron jobs — must be manually recreated or exported/imported
- [ ] Plugin config — a2a-gateway peers, tokens
- [ ] /etc/hosts entries — mesh DNS

### 5. Workspace State
- [ ] All projects/ directories
- [ ] scripts/ — send scripts, peer configs
- [ ] peers.json — A2A peer addresses

### 6. Services
- [ ] Managed service unit files (launchd on macOS, systemd on Linux)
- [ ] Ollama/llama.cpp model files
- [ ] Any background processes

---

## Pre-Migration Checklist (to be completed before ANY migration)

- [ ] All three agents have reviewed and agreed on the migration plan via A2A
- [ ] Woodhouse has synthesised the consensus and received Mr. Ross approval
- [ ] Source node inventory complete (list all files, services, credentials)
- [ ] Target node confirmed accessible and healthy
- [ ] Backup of source node state created
- [ ] Rollback plan documented

## Migration Sequence

1. **Inventory** — catalogue every element in the list above on the source node
2. **Consensus** — all three agents review the plan; Woodhouse delivers to Mr. Ross
3. **Mr. Ross approves** — explicit sign-off before any action
4. **Transfer** — move files, recreate services, test each element
5. **Validate individually** — confirm each element works on the new node
6. **Validate collectively** — A2A test, heartbeat test, cron test
7. **Post-mortem** — document what worked, what didn't, what was missed

---

## Known Failure Modes (from incidents)

| Element | What Was Missed | Impact |
|---|---|---|
| auth-profiles.json | Not transferred → all models 401 | Agent inoperative |
| Cron jobs | Not recreated → scheduled tasks lost | Silent failures |
| /etc/hosts | Not added on new node → DNS failures | A2A unreliable |
| Persona files | Not transferred → agent lost identity | Incorrect behaviour |
| openclaw.json model config | Not updated for new node's auth | Wrong model used |
| Managed services | Not created → processes not auto-starting | Node goes dark after reboot |

*This table will be expanded as Liz's post-mortem on Ray's migration is received.*

---

## Post-Mortem: Ray Migration Incident (2026-04-07)
*Status: PENDING — Liz input requested*

Details to be filed once Liz's account is received.

---
*Next review: after Liz post-mortem is filed*

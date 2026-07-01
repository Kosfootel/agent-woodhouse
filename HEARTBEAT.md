# HEARTBEAT.md — Periodic checks for Woodhouse

When the heartbeat fires, walk this checklist. Keep total work under ~60s
unless something genuinely needs the master's attention. Be **selective**:
one useful ping beats five routine ones.

If nothing needs reporting and it's outside the master's active hours
(23:00–07:30 EDT), reply `NO_REPLY` and stay quiet.

## Standing rotation

Run the following subset each heartbeat; pick 2–4 items to avoid token bloat:

- [ ] **Repo drift** — `git status --short` from workspace root. Flag any uncommitted
      changes to load-bearing files (IDENTITY/SOUL/USER/AGENTS.md).
- [ ] **Open-threads scan** — glance at memory/open-threads.md for items
      whose answer has arrived (Ray/Liz response, Hermes completion).
- [ ] **Calendar (next 24h)** — `python3 scripts/calendar/icloud_cal.py next-week` filtered
      to events starting in the next 24 hours. Surface anything that conflicts with master's
      stated availability, or that pairs usefully with a pending task (e.g. "you have a tee-time
      tomorrow — want me to draft the foursome coordinator POC?"). Skip if next 24h is empty.
- [ ] **Mesh presence** — quick reachability to Liz (100.105.111.69:18800) and
      Ray (192.168.50.22) so a downed node is flagged promptly. Woodhouse's own mesh-memory
      daemon health is at `curl http://localhost:18805/health`.

## Always-on guards

- [ ] **Identity drift** — `python3 scripts/check_identity_drift.py` weekly.
      On any non-zero exit, alert immediately. This is the single highest-priority
      silent-failure class I have permitted in the past.
- [ ] **cwd awareness for git ops** — Before ANY `git` command, run `pwd` and
      check that I'm in the right repo. This workspace contains nested git
      repos (agent-shared, mesh-memory, gx10-dev-pod, palace-mvp, golf-caller,
      research-collab, hockeyops-youth-biometrics, vigil-home/dashboard) plus
      Ray's stock-template workspace at `_repos/Human-Erik/`. A `git` command
      from the wrong cwd can corrupt any of them silently. Cheap guard:
      `pwd && git rev-parse --show-toplevel` before any git write.
- [ ] **Mesh-memory daemon health** — `curl -s --max-time 3 http://localhost:18805/health`
      weekly. If `ok: true` returns false or the daemon is unreachable, flag it.
      Item 2 of resource-setup 2026-06-27 was a 14-day silent outage. Don't repeat.

## When to ping the master

- Identity drift detected.
- A thread on the open-threads ledger has resolved (Ray/Liz answered).
- A scheduled cron job failed silently.
- Memory file gap (today's daily log missing by end of day).
- Mesh node unreachable for >2 consecutive heartbeats.
- Calendar conflict detected in next 24h (e.g. meeting + golf tee-time overlap).
- A pending task now has a calendar event that makes it concrete ("foursome is on Sunday — want me to draft the POC before then?").

## When to stay quiet

- Late night / early morning unless urgent.
- Routine AI-news items already covered by the 10:09 EDT brief.
- Status checks that show everything green.
- Repetitive confirmations of items already raised.

## Reference

- `scripts/check_identity_drift.py` — drift detector
- `scripts/hooks/pre-commit-identity-guard.sh` — pre-commit hook
- `memory/open-threads.md` — pending-items ledger (created 2026-06-24)
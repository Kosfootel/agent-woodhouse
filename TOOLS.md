# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Report Storage Conventions

| Report Type | Repository | Path Pattern |
|-------------|------------|--------------|
| General research/analysis | `agent-woodhouse` | `/research/YYYY-MM-DD-topic.md` |
| Development/project-specific | `gx-10-dev-pod` | `/plans/`, `/reviews/`, `/specs/` |
| Lossless-claw diagnostics | `agent-woodhouse` | `/docs/diagnostics/` |
| Daily briefs | `agent-woodhouse` | `/briefs/YYYY-MM-DD-{time}.md` |

### Quick Reference

- **agent-woodhouse** → `https://github.com/Kosfootel/agent-woodhouse.git`
  - AI trends, research, analysis, general reporting
  - Lossless-claw diagnostics and health reports
  - Daily news briefs

- **gx-10-dev-pod** → `https://github.com/Better-Machine/gx-10-dev-pod.git`
  - Code Review & Architecture Agent plans
  - Development project specifications
  - Technical reviews and architecture decisions

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

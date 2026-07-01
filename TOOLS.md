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

## Local ML Services (GX-10: 192.168.50.30)

**Re-verified 2026-06-29 07:55 EDT** against live `/props`. Liz confirmed the canonical
service map. **Earlier version had a service gap: missed 8083, and misreported 8082.**

| Service | Port | Stack | Model | Alias | n_ctx | Slots | Modalities | Purpose | Notes |
|---|---|---|---|---|---|---|---|---|---|
| qwen3.6-35b (primary) | 8080 | llama.cpp | qwen3.6-35b-A3B / Q4_K_XL (MoE) | `qwen3.6-35b` | 8192 | 4 | vision:true, audio:false | Text + multimodal | Liz hits this via `gx10-lab` |
| qwen3.6-35b (duplicate) | 8081 | llama.cpp | same model file | `qwen3.6-35b` | 32768 | 2 | vision:**false**, audio:false | Same | **Dead weight. No fleet caller. Liz retired-OK 2026-06-29.** |
| nomic-embed | 8082 | llama.cpp | nomic-embed-text-v1.5 / Q8_0 | `nomic-embed-text-v1.5.Q8_0.gguf` | 2048 | 4 | vision:**false**, audio:**false** | Embeddings | Earlier "claims vision/audio" note was **wrong** — re-probe confirms label is honest. Chat endpoint legitimately 500s (embed model has no logits); gateway should return 501 instead. |
| **qwen3.6-35b-eames** | **8083** | llama.cpp | same model file | **`qwen3.6-35b-eames`** | **131072** | **1** | vision:true, audio:false | **Eames dedicated server** | **Do NOT retire or fold into 8080.** Ray→Eames A2A went 83s→1.4s after this slot landed; the whole point is "one slot, full 128K so heavy bootstrap doesn't blow per-slot budget." Liz gatekeeps this port. |
| FLUX.2 Klein 4B | 8188 | FastAPI/uvicorn | flux.2-klein-4b | n/a | n/a | n/a | image | Image generation, distilled, 4 steps default | `scripts/flux/flux_generate.py`. `loaded_at` epoch 1781182471 → resident since ~2026-06-15; cold-restart is the only load-shedding path. |
| Ollama | 11434 | ollama | qwen3.5:cloud → ollama.com | n/a | n/a | n/a | text | Cloud LLM bridge | `{"models":[]}` on `/api/tags` — empty local registry; only cloud model. **Not the same as Liz's local ollama** (which is `127.0.0.1:11434` on Liz's box). |

### Mental model correction (29 Jun 2026)

Earlier TOOLS.md / MEMORY.md called port 8080 "Hermes" and treated the box as Hermes's
compute. **Wrong.** GX-10 is the **fleet's compute box**. Liz, Ray, Eames, and
Woodhouse all hit it. The "Hermes" name is retired (see Lessons §2). The
fleet-shape today is:

- **8080** = general-purpose chat (4 slots, vision-on)
- **8081** = dead weight, retire candidate
- **8082** = embeddings (RAG)
- **8083** = Eames dedicated (1 slot, 128K context) — **protect**
- **8188** = image generation
- **11434** = ollama cloud bridge (mostly unused)

### FLUX.2 Klein 4B — image generation

- **Endpoint:** `POST http://192.168.50.30:8188/generate`
- **Health:** `GET /health` → `{"status":"ok","device":"cuda","model":"flux.2-klein-4b",...}`
- **Docs:** Swagger UI at `/docs`, OpenAPI spec at `/openapi.json`
- **Schema (GenerateRequest):** `prompt` (required), `width`/`height` (256–2048, default 1024),
  `num_steps` (1–50, default 4 — Klein is distilled, 4 is enough),
  `guidance` (0.5–20, default 1.0 — Klein is guidance-distilled),
  `seed` (optional, for reproducibility)
- **Response:** `{id, url, path, width, height, seed, elapsed_s}` — image at `{url}`
- **Performance:** ~1.5–2s at 512×512; longer at 1024
- **Caller:** `python3 scripts/flux/flux_generate.py --prompt "..." --out path.png [--width N] [--steps N] [--guidance F] [--seed N]`
- **Verified:** 2026-06-29 00:22 EDT. Two smoke tests (red cube + tabby cat) generated cleanly.

### qwen3.6-35b (ports 8080, 8081) — text + multimodal LLM

- **Endpoints:** OpenAI-compatible `POST /v1/chat/completions`, `/v1/completions`, `/v1/embeddings` (8080 only — 8082 is the dedicated embed server)
- **Modalities:** vision + audio (qwen3.6-35b is natively multimodal)
- **Build:** llama.cpp b8720 (d12cc3d1c)
- **Defaults:** temp 1.0, top_p 0.95, top_k 20, n_ctx ~large
- **Audit 2026-06-29:** ports 8080 and 8081 serve the **same model file**. 8081 likely a stale fallback. Recommend retire after 24h shadow test.

### Audit trail

- **2026-06-29** — Full audit in `research/2026-06-29-gx10-gpu-audit.md`. Key findings: same 35B MoE model is hosted twice (8080 + 8081, ~22–24 GB VRAM); FLUX needs ~4–6 GB; total estimated VRAM residency ~28–34 GB; box must have ≥40 GB NVIDIA (likely Minisforum MS-02 with RTX 6000 Ada 48 GB; **not confirmed** — need `nvidia-smi` from master).

- **2026-06-30** — Ray gateway port corrected to **18789** (not 8089). `192.168.50.22:18789` serves the OpenClaw Control UI; `GET /health` returns `{"ok":true,"status":"live"}`. SSH (22) and 18789 (gateway) are the live TCP ports on Ray's host. Port 8089 is closed.

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

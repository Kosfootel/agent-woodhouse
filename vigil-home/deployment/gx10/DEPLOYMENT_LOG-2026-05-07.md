# Vigil Home — GX-10 Deployment Log

**Date:** 2026-05-07  
**Time:** 21:04–21:30 EDT  
**Deploying Agent:** Woodhouse subagent  
**Target:** 192.168.50.30 (Asus Ascent GX-10, DGX OS aarch64)

---

## Summary

Vigil Home (IoT threat detection backend) successfully deployed to GX-10 as a 3-container Docker stack.

### Service: 192.168.50.30:8000
### Swagger Docs: http://192.168.50.30:8000/docs

---

## Deployment Process

### 1. Access Discovery
- Initially had no SSH access to GX-10
- NVIDIA Sync (`/Users/FOS_Erik/Library/Application Support/NVIDIA/Sync/config/nvsync.key`) had a provisioned SSH key
- Connected via `erik-ross@192.168.50.30` using the nvsync key

### 2. Architecture Issue
- First build was `amd64` (Ray's architecture)
- GX-10 is `aarch64` (ARM64)
- **Solution:** Used Docker buildx with QEMU binfmt on Ray to cross-compile for arm64

### 3. Image Registry
- Set up local Docker registry on Ray (192.168.50.22:5000)
- Built arm64 image pushed as `192.168.50.22:5000/vigil-api:arm64`
- GX-10 configured with `insecure-registries` to pull from LAN registry

### 4. Compose Changes
- Replaced `build:` directive with pre-built image reference
- Changed Suricata interface from `eth0` → `enP7s7` (GX-10's primary interface)
- Updated Suricata image to `jasonish/suricata:7.0.7` (newer, has aarch64 support)
- Added `platform: linux/arm64` to postgres image
- Removed dashboard profile (not yet built)

### 5. Container Status

| Container | Image | Status |
|-----------|-------|--------|
| vigil-api | 192.168.50.22:5000/vigil-api:arm64 | Running (health: starting) |
| vigil-db | postgres:15-alpine | Healthy |
| vigil-suricata | jasonish/suricata:7.0.7 | Running |

### 6. Verification
- ✅ `/devices` endpoint returns device list (11 auto-detected devices)
- ✅ `/classify/{mac}` endpoint returns classifications
- ✅ `/events`, `/alerts`, `/baseline` endpoints all functional
- ✅ Swagger docs accessible at `/docs`
- ✅ systemd service installed and enabled

### 7. systemd Service
- Installed at `/etc/systemd/system/vigil-api.service`
- Modified `docker-compose` → `docker compose` for v2 compatibility
- Enabled for auto-start on boot

---

## Configuration Details

**Interface:** `enP7s7` (NVIDIA ConnectX-7 NIC)  
**Container Network:** `vigil-network` (bridge)  
**API Port:** 8000  
**Database:** PostgreSQL 15 (internal to Docker network)  
**Suricata Mode:** Host network mode for packet capture  
**Memory Limits:** API=512M, DB=512M, Suricata=1G

## Issues / Notes
- No `/health` endpoint in the POC backend — Docker healthcheck uses `/devices` instead
- Password set via .env or POSTGRES_PASSWORD env var — currently defaulting to blank
- Docker registry on 192.168.50.22:5000 is temporary; should push to Docker Hub for persistence
- GX-10 runs DGX OS (Ubuntu-based, aarch64) with 128GB unified memory
- Flux 2 model server and llama.cpp (nemotron-super-120b) continue running alongside Vigil

## Next Steps
1. Set a proper database password (POSTGRES_PASSWORD env var)
2. Push Vigil API image to Docker Hub for permanent registry
3. Set up Suricata rule configuration (suricata.yaml)
4. Configure alert notifications (email/Telegram)
5. Build and deploy the dashboard (optional, profile-based)

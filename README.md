# Vigil Home Security — GX-10 Prototype

**Status:** Active Development  
**Environment:** GX-10 (192.168.50.30)  
**Target:** Jetson Nano/Orin Nano (4GB RAM)  

---

## Quick Links

| Service | URL | Status |
|---------|-----|--------|
| Dashboard | http://192.168.50.30:8085/vigil/ | ✅ Live |
| API | http://192.168.50.30:8005/ | ✅ Live |
| Backend Health | http://192.168.50.30:8005/health | ✅ 200 OK |

---

## Architecture

```
GX-10 (Prototype) → Jetson (Production)

┌─────────────────────────────────────┐
│  Vigil Dashboard (Next.js + nginx)   │
│  Port: 8085                         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Caddy Reverse Proxy               │
│  Ports: 8005 (API), 8085 (UI)       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  FastAPI Backend                   │
│  Port: 8000 (internal)              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  SQLite Database (vigil.db)         │
│  Location: ~/vigil/data/vigil.db    │
└───────────────────────────────────────┘
```

---

## Database Schema

**Location:** `~/vigil/data/vigil.db`

| Table | Purpose |
|-------|---------|
| `devices` | Core device registry (MAC, IP, trust_score, myhomeid_reference) |
| `device_observations` | Multi-source observations (Suricata, router, manual) |
| `alerts` | Security alerts with severity levels |
| `network_flows` | Traffic pattern tracking |
| `myhomeid_sync` | Clean Slate (myhomeid) integration state |
| `router_config` | Encrypted router credentials |
| `agent_logs` | Agency agent activity tracking |

**Schema:** See `vigil_schema.sql`  
**Sample Queries:** See `vigil_queries.sql`

---

## Agency Agents

**Location:** `~/vigil/agents/`

### Router Monitor Agent
```bash
cd ~/vigil/agents
python3 test_router_monitor.py <username> <password>
```

Scrapes device list from ASUS GT6 router and stores in database.

### Future Agents
- `network_monitor_agent.py` — Suricata log processor
- `device_identity_agent.py` — myhomeid sync
- `security_analyst_agent.py` — Anomaly detection

---

## Development Workflow

### 1. Start Services
```bash
# Containers are auto-started via Docker Compose
docker ps | grep vigil
```

### 2. Test Router Integration
```bash
cd ~/vigil/agents
python3 test_router_monitor.py admin <password>
```

### 3. Query Database
```bash
sqlite3 ~/vigil/data/vigil.db < vigil_queries.sql
```

### 4. View Logs
```bash
# Dashboard
docker logs vigil-tier-a-dashboard

# Backend
docker logs vigil-tier-a-backend

# Caddy
docker logs vigil-tier-a-caddy
```

---

## Git Repository

**Repo:** `Kosfootel/agent-woodhouse`  
**Branch:** `hermes/vigil-playbooks-models`

```bash
git status
git add <files>
git commit -m "message"
git push origin hermes/vigil-playbooks-models
```

---

## Roadmap

### Phase 1: Foundation (Current)
- ✅ Environment cleanup
- ✅ Unified database schema
- ✅ Router monitor agent
- ⏳ Connect dashboard to database
- ⏳ Manual device entry UI

### Phase 2: Integration
- ⏳ myhomeid API integration
- ⏳ Suricata agent
- ⏳ Device correlation (router + Suricata)
- ⏳ Alert generation

### Phase 3: Jetson Deployment
- ⏳ ARM64 container builds
- ⏳ SQLite optimization
- ⏳ Resource profiling
- ⏳ Field testing

---

## Troubleshooting

### Dashboard 404
```bash
docker restart vigil-tier-a-caddy
docker restart vigil-tier-a-dashboard
```

### Database Locked
```bash
# SQLite WAL mode handles concurrency
# Check for long-running queries:
sqlite3 ~/vigil/data/vigil.db ".tables"
```

### Router Authentication Fails
- Verify router IP: `ping 192.168.50.1`
- Check credentials in Bitwarden
- Ensure router web interface is enabled

---

## Resources

- [ASUS GT6 Documentation](https://www.asus.com/networking-iot-servers/wifi-routers/asus-zenwifi-pro-et12/)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Last Updated:** 2026-05-20  
**Maintainer:** Woodhouse

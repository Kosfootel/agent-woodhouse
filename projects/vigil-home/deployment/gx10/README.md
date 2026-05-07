# Vigil Home — GX-10 Deployment Configuration

## Overview
Production-ready Docker Compose for Asus Ascent GX-10 (192.168.50.30)

## Resource Allocation
- **CPU:** Minimal (Suricata moderate load)
- **RAM:** ~1GB reserved
- **Storage:** 10GB for logs/database
- **Network:** Host mode for Suricata promiscuous capture

## Services

### vigil-api
- FastAPI backend with AI modules
- Port: 8000 (LAN accessible)
- Postgres database (migrated from SQLite)
- Health endpoint: `/health`

### vigil-suricata
- Network IDS with full rule sets
- Host network mode for packet capture
- Eve.json output to shared volume
- Log rotation: 7 days

### vigil-db
- Postgres 15 (if headroom allows)
- Alternative: SQLite for minimal footprint
- Persistent volume: `vigil-data`

### vigil-dashboard (optional)
- React frontend
- Port: 3000
- Can be disabled if headroom tight

## Quick Start

```bash
# On GX-10
cd /opt/vigil
docker-compose -f docker-compose.gx10.yml up -d

# Check status
docker-compose ps
curl http://localhost:8000/health
```

## Monitoring

| Endpoint | Purpose |
|----------|---------|
| `192.168.50.30:8000` | Vigil API |
| `192.168.50.30:8000/docs` | Swagger docs |
| `192.168.50.30:8000/metrics` | Prometheus metrics |

## Log Locations
- Suricata: `/var/log/vigil/suricata/`
- API: `docker logs vigil-api`
- Database: Persistent volume `vigil-postgres-data`

## Backup
Database backup script runs daily at 02:00 → `/opt/vigil/backups/`

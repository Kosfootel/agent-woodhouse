# Vigil CI/CD Pipeline Documentation

**Repository:** `Kosfootel/agent-woodhouse`  
**Branch:** `hermes/vigil-playbooks-models`  
**Deployment Target:** GX-10 (192.168.50.30)  
**Last Updated:** 2026-05-25

---

## Overview

This document describes the complete CI/CD pipeline for the Vigil dashboard application. The pipeline automates building Docker images, pushing them to GitHub Container Registry (GHCR), and deploying them to the GX-10 production server.

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Security     │───▶│ Build        │───▶│ Deploy       │              │
│  │ Scan         │    │ Images       │    │ to GX-10     │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│   Trivy Scans        GHCR Registry        SSH + Docker                 │
│   SARIF Reports      Multi-arch           Auto-rollback                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              GX-10 Server                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  GitHub Container Registry (ghcr.io)                               │ │
│  │  ┌──────────────────┐    ┌──────────────────┐                    │ │
│  │  │ Backend Image    │    │ Dashboard Image  │                    │ │
│  │  │ :{sha} :latest   │    │ :{sha} :latest   │                    │ │
│  │  └──────────────────┘    └──────────────────┘                    │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                    │                                    │
│                                    ▼                                    │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Docker Compose (docker-compose.cicd.yml)                        │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │ │
│  │  │ vigil-      │    │ vigil-      │    │ vigil-frontend      │   │ │
│  │  │ backend     │───▶│ dashboard   │───▶│ (Caddy/Nginx)       │   │ │
│  │  │ :8000       │    │ :8085       │    │ :80/:443            │   │ │
│  │  └─────────────┘    └─────────────┘    └─────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Files Created

| File | Purpose |
|------|---------|
| `.github/workflows/dashboard-deploy.yml` | GitHub Actions workflow for CI/CD |
| `docker-compose.cicd.yml` | Docker Compose for GHCR-based deployments |
| `scripts/deploy-gx10.sh` | Standalone deployment script for GX-10 |
| `VIGIL_CICD.md` | This documentation |

---

## Workflow Stages

### Stage 1: Security Scanning

- **Trivy** vulnerability scanner for both dashboard and backend
- Scans for CRITICAL and HIGH severity issues
- Results uploaded to GitHub Security tab via SARIF format
- Pipeline continues even if scan finds issues (for visibility)

### Stage 2: Build & Push

- **Build Dashboard Image:**
  - Context: `./dashboard`
  - Tag: Git commit SHA + `latest`
  - Multi-arch: `linux/amd64`, `linux/arm64`
  - Cache: GitHub Actions cache

- **Build Backend Image:**
  - Context: `./backend`
  - Tag: Git commit SHA + `latest`
  - Multi-arch: `linux/amd64`, `linux/arm64`
  - Cache: GitHub Actions cache

### Stage 3: Deploy to GX-10

- SSH into GX-10 using stored secret key
- Pull images from GHCR
- Update running containers via `docker-compose.cicd.yml`
- Health checks on both services
- Automatic rollback on failure
- Cleanup old images

---

## GitHub Secrets Required

Configure these secrets in your repository settings:

| Secret | Description | How to Create |
|--------|-------------|---------------|
| `GX10_SSH_KEY` | Private SSH key for GX-10 access | `ssh-keygen -t ed25519 -C "github-actions"` then add public key to `~/.ssh/authorized_keys` on GX-10 |
| `GITHUB_TOKEN` | Auto-provided by GitHub | No action needed |

### Setting up GX-10 SSH Access

On your local machine:
```bash
# Generate deployment key (if not exists)
ssh-keygen -t ed25519 -C "vigil-deploy" -f ~/.ssh/vigil_deploy

# Copy public key to GX-10
cat ~/.ssh/vigil_deploy.pub | ssh erik-ross@192.168.50.30 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

On GitHub:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GX10_SSH_KEY`
4. Value: Paste contents of `~/.ssh/vigil_deploy`

---

## Deployment Triggers

The workflow runs on:

1. **Push to `hermes/vigil-playbooks-models` branch**
   - Only when files in `dashboard/`, `backend/`, `docker-compose.yml`, or the workflow itself change

2. **Manual trigger (workflow_dispatch)**
   - Go to Actions → Vigil Dashboard CI/CD → Run workflow
   - Choose environment: `production` or `staging`

---

## Image Registry

Images are stored at:
```
ghcr.io/Kosfootel/agent-woodhouse-dashboard:{sha}
ghcr.io/Kosfootel/agent-woodhouse-dashboard:latest
ghcr.io/Kosfootel/agent-woodhouse-backend:{sha}
ghcr.io/Kosfootel/agent-woodhouse-backend:latest
```

### Making Images Public (Required for CI/CD)

1. Go to https://github.com/users/Kosfootel/packages
2. Click on each package
3. Click "Package settings"
4. Under "Danger Zone" → "Change package visibility"
5. Select "Public"

---

## Local Deployment (Manual)

If you need to deploy manually from GX-10:

```bash
# Navigate to project directory
cd ~/projects/vigil-home

# Run deployment script
./scripts/deploy-gx10.sh

# Or with specific tag
IMAGE_TAG=abc1234 ./scripts/deploy-gx10.sh

# Check status
./scripts/deploy-gx10.sh --status

# Rollback if needed
./scripts/deploy-gx10.sh --rollback
```

---

## Docker Compose Configuration

The `docker-compose.cicd.yml` uses environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_TAG` | `latest` | Image tag to deploy (commit SHA) |
| `REGISTRY` | `ghcr.io` | Container registry |
| `REPO_OWNER` | `Kosfootel` | GitHub owner/org |

Example with custom values:
```bash
IMAGE_TAG=abc1234 REGISTRY=ghcr.io REPO_OWNER=Kosfootel docker compose -f docker-compose.cicd.yml up -d
```

---

## Health Checks

Services include built-in health checks:

- **Backend:** `wget --spider http://localhost:8000/health`
  - Interval: 30s
  - Timeout: 10s
  - Retries: 3

- **Dashboard:** `wget --spider http://localhost:8085/`
  - Interval: 30s
  - Timeout: 10s
  - Retries: 3

---

## Monitoring Endpoints

| Endpoint | Purpose |
|----------|---------|
| http://192.168.50.30:8085 | Vigil Dashboard |
| http://192.168.50.30:8000/health | Backend health check |
| http://192.168.50.30:8000/api/devices | Device list API |

---

## Troubleshooting

### Deployment Fails

Check GitHub Actions logs for specific error. Common issues:

1. **SSH connection failed**
   - Verify `GX10_SSH_KEY` secret is set correctly
   - Ensure GX-10 is reachable from GitHub Actions runners

2. **Image pull failed**
   - Images must be public or `GITHUB_TOKEN` must have package:read scope
   - Check GHCR package visibility settings

3. **Health check failed**
   - Check container logs: `docker logs vigil-backend`
   - Check container status: `docker ps`

### Manual Recovery

If deployment gets stuck:

```bash
# On GX-10
ssh erik-ross@192.168.50.30

cd ~/projects/vigil-home

# Check status
docker compose -f docker-compose.cicd.yml ps

# View logs
docker logs vigil-backend
docker logs vigil-dashboard

# Restart services
docker compose -f docker-compose.cicd.yml restart

# Full reset
docker compose -f docker-compose.cicd.yml down
docker compose -f docker-compose.cicd.yml up -d
```

---

## Security Considerations

1. **SSH Key:** Use dedicated deployment key, not personal SSH key
2. **Images:** Consider signing images with Cosign for supply chain security
3. **Secrets:** Never commit secrets to repository
4. **Network:** GX-10 should be on private network (192.168.50.0/24)
5. **Updates:** Regularly update base images to patch vulnerabilities

---

## Future Enhancements

- [ ] Add staging environment
- [ ] Implement blue-green deployments
- [ ] Add automated integration tests
- [ ] Set up Prometheus/Grafana monitoring
- [ ] Add image signing with Cosign
- [ ] Implement canary deployments
- [ ] Add Slack notifications for deployments

---

## Related Documentation

- `VIGIL_DEPLOYMENT_REPORT.md` - Previous deployment status
- `VIGIL_DISCOVERY_ENHANCED.md` - Discovery system documentation
- `VIGIL_SECURITY_ARCHITECTURE.md` - Security architecture

---

*CI/CD Pipeline created by DevOps Automator Agent*  
*Last updated: 2026-05-25*

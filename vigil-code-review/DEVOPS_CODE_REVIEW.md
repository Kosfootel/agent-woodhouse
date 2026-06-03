# Vigil Dashboard - DevOps Infrastructure Code Review

**Date:** 2026-05-26  
**Reviewer:** DevOps Infrastructure Reviewer Agent  
**Scope:** Docker, CI/CD, Deployment Configuration, Security, Infrastructure  
**Target:** `/Users/FOS_Erik/.openclaw/workspace/vigil-work/`

---

## Executive Summary

This review covers the deployment, CI/CD, and infrastructure configuration for the Vigil Dashboard project. The system is deployed to GX-10 (192.168.50.30) using Docker containers managed by Docker Compose, with GitHub Actions providing automated CI/CD pipelines.

### Overall Assessment: **MIXED - REQUIRES ATTENTION**

The infrastructure has working CI/CD and deployment scripts, but contains **critical security issues**, **configuration drift**, and **missing hardening** that must be addressed before production use.

---

## 1. Docker Configuration

### 1.1 Dockerfile Analysis

#### Backend Dockerfile (`/backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default port
ENV PORT=8000

# Run the FastAPI application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

**Issues Found:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 1 | No image digest pinning | **MEDIUM** | Use `python:3.11-slim@sha256:...` for reproducible builds |
| 5-7 | `curl` and `iproute2` installed but may not be needed in production | **LOW** | Remove or move to multi-stage build |
| 14 | Application runs as root | **HIGH** | Create non-root user and use `USER` directive |
| 20 | `CMD` uses shell form which doesn't handle signals properly | **MEDIUM** | Use JSON array form: `CMD ["uvicorn", ...]` |
| Missing | No HEALTHCHECK defined | **MEDIUM** | Add healthcheck for container orchestration |
| Missing | No `.dockerignore` file present | **LOW** | Create to prevent sensitive files from being copied |

**Positive Aspects:**
- Uses `--no-install-recommends` to reduce image size
- Properly cleans up apt cache
- Uses `--no-cache-dir` for pip
- Multi-arch support (linux/amd64, linux/arm64) in CI/CD

---

#### Dashboard Dockerfile (`/dashboard/Dockerfile`)

```dockerfile
FROM nginx:alpine

# Copy built React static files
COPY build/ /usr/share/nginx/html/

# Create custom nginx config
RUN echo 'server { \
    listen 8085; \
    ...
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8085

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8085/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**Issues Found:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 1 | No image digest pinning | **MEDIUM** | Pin to specific digest |
| 4 | Inline nginx config via RUN/echo is fragile | **MEDIUM** | Use COPY from separate config file |
| 4 | Hardcoded backend IP (192.168.50.30:8000) | **HIGH** | Use environment variable |
| 6-18 | Complex string escaping prone to errors | **LOW** | Use heredoc or external file |
| Missing | Nginx runs as root by default | **HIGH** | Configure non-root nginx user |

**Positive Aspects:**
- Healthcheck is properly defined
- Uses JSON array CMD form (correct)
- Alpine-based for smaller footprint

---

#### POC Backend Dockerfile (`/projects/vigil-home/poc-backend/Dockerfile`)

**Issues Found:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 1 | Uses different Python version (3.12) than main backend (3.11) | **MEDIUM** | Standardize Python versions |
| 19 | CMD uses shell form | **MEDIUM** | Use JSON array form |

---

### 1.2 Docker Compose Analysis

#### Main Compose File (`/docker-compose.yml`)

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: vigil-backend
    hostname: backend
    network_mode: host  # ⚠️ SECURITY RISK
    environment:
      - VIGIL_ENV=production
      - DATABASE_PATH=/app/data/vigil.db
      - POLICY_PATH=/app/policy.yaml
      - PORT=8000
      - HOST=0.0.0.0
    volumes:
      - ./backend/data:/app/data:rw
      - ./backend/policy.yaml:/app/policy.yaml:ro
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

**Critical Issues:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 8 | `network_mode: host` exposes containers to host network | **CRITICAL** | Use Docker networks with explicit port mapping |
| 14 | Database path uses relative path on host | **MEDIUM** | Use named volumes or absolute paths |
| Missing | No secrets management | **HIGH** | Use Docker secrets or external vault |
| Missing | No logging configuration | **LOW** | Configure log drivers and rotation |
| Missing | No healthcheck defined | **MEDIUM** | Add healthcheck for monitoring |

**Why `network_mode: host` is CRITICAL:**
- Bypasses Docker's network isolation
- Containers can access all host network interfaces
- Makes port mapping ineffective
- Increases attack surface significantly
- Prevents use of Docker DNS/service discovery

---

#### CI/CD Compose File (`/docker-compose.cicd.yml`)

**Positive Aspects:**
- Uses pre-built images from GHCR (good for CI/CD)
- Healthchecks defined for both services
- Logging configuration with rotation
- Resource limits configured
- `depends_on` with health condition

**Issues:**

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| Still uses `network_mode: host` | **CRITICAL** | Remove network_mode, use explicit port mapping |
| Database volumes use relative paths | **MEDIUM** | Use named volumes |
| No secrets for GHCR auth in compose | **MEDIUM** | Document how credentials are managed |

---

#### Backup Compose File (`/docker-compose.yml.bak`)

**CRITICAL BUG FOUND:**

| Line | Issue | Severity |
|------|-------|----------|
| 20 | `healthcheck` uses `http://localhost:808000/health` - Invalid port | **CRITICAL** |
| 46 | `healthcheck` uses `http://localhost:808080/` - Invalid port | **CRITICAL** |

These typos (`808000` and `808080` instead of `8000` and `8080`) would cause health checks to always fail.

**Other Issues:**
- Uses custom bridge network with fixed subnet (potential conflicts)
- Caddy mounts Tailscale certs (specific to host setup)
- Missing health check for Caddy

---

#### GX-10 Compose File (`/projects/vigil-home/deployment/gx10/docker-compose.gx10.yml`)

**Issues:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 7 | Suricata container uses `network_mode: host` with `NET_ADMIN` | **HIGH** | Required for IDS but document security implications |
| 23 | Hardcoded database password | **CRITICAL** | Use environment variable or Docker secret |
| 37 | `vigil-dashboard` uses profile that may not be enabled | **LOW** | Document how to enable |

---

### 1.3 Caddy Configuration (`/Caddyfile.spa`)

```caddy
# Dashboard frontend
:8080 {
    header {
        Access-Control-Allow-Origin "*"
        ...
    }
    reverse_proxy dashboard:8080
}
```

**Issues:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 5 | CORS `Access-Control-Allow-Origin: *` is overly permissive | **MEDIUM** | Restrict to specific origins |
| 16 | Reverse proxy to `dashboard:8080` assumes Docker DNS | **LOW** | Document network requirements |
| 21 | Admin API exposed on `:2019` | **MEDIUM** | Restrict to localhost or add auth |
| Missing | No TLS configuration | **MEDIUM** | Add automatic HTTPS |

---

## 2. CI/CD Pipeline Analysis

### 2.1 GitHub Actions Workflow (`.github/workflows/dashboard-deploy.yml`)

**Pipeline Stages:**
1. Security Scan (Trivy)
2. Build Dashboard Image
3. Build Backend Image
4. Deploy to GX-10

**Positive Aspects:**
- Multi-stage pipeline with security scanning
- Trivy vulnerability scanning with SARIF upload
- Multi-arch builds (amd64 + arm64)
- Image caching with GitHub Actions cache
- Automated rollback on failure
- Proper health checks after deployment
- Resource limits on jobs

**Issues:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 30 | Trivy uses `@master` - unpinned action | **MEDIUM** | Pin to specific version/commit SHA |
| 46, 81 | `actions/checkout@v4` - good, properly pinned to major | **INFO** | Consider pinning to SHA for reproducibility |
| 119 | `docker/setup-buildx-action@v3` - good | **INFO** | - |
| 139 | `npm ci` with `CI=false` bypasses CI checks | **MEDIUM** | Document why CI=false is needed |
| 142 | Hardcoded `REACT_APP_API_URL` | **MEDIUM** | Use environment variable |
| 205 | `StrictHostKeyChecking no` - security risk | **HIGH** | Use known_hosts or ssh-keyscan |
| 207 | `UserKnownHostsFile /dev/null` - security risk | **HIGH** | Properly manage known hosts |
| 217 | GHCR token passed via environment | **MEDIUM** | Ensure secrets are masked in logs |
| 226 | Uses `docker compose` without `-f` flag | **LOW** | Explicitly specify compose file |

---

### 2.2 Deployment Scripts

#### `/deploy.sh`

**Issues:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 9 | `StrictHostKeyChecking=no` in SSH_OPTS | **HIGH** | Remove, use known_hosts |
| 18 | No timeout handling for rsync | **LOW** | Add timeout and retry logic |
| 24 | `timeout 30 rsync` - arbitrary timeout | **LOW** | Increase or remove for large transfers |
| 35 | Stops and removes all containers | **MEDIUM** | Use rolling update instead |
| 40 | No health check timeout | **LOW** | Add proper health check loop |

#### `/scripts/deploy-gx10.sh`

**Positive Aspects:**
- Comprehensive logging with colors
- Rollback functionality
- Health check with retry logic
- Prerequisites checking
- Image cleanup

**Issues:**

| Line | Issue | Severity | Recommendation |
|------|-------|----------|----------------|
| 22 | Default values for sensitive variables | **LOW** | Fail if required vars not set |
| 45 | Comment about running on GX-10 but allows override | **MEDIUM** | Validate host or enforce REMOTE_DEPLOY |
| 140 | `trap '...' ERR` may not catch all failures | **LOW** | Also trap EXIT and SIGTERM |

---

## 3. Security Analysis

### 3.1 Secrets Management

**CRITICAL FINDINGS:**

| File | Line | Issue |
|------|------|-------|
| `/projects/vigil-home/poc-backend/docker-compose.yml` | 17 | **EXPOSED CREDENTIALS:** `GMAIL_APP_PASSWORD=odsq hraj soqe hyzm` |
| `/projects/vigil-home/poc-backend/docker-compose.yml` | 16 | **EXPOSED EMAIL:** `GMAIL_USER=kosfootel@gmail.com` |

**These credentials must be rotated immediately.**

**Recommendations:**
1. Rotate the Gmail App Password immediately
2. Move all secrets to environment variables or Docker secrets
3. Use a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.)
4. Add `.env` files to `.gitignore` if not already present

### 3.2 Network Security

| Issue | Severity | Description |
|-------|----------|-------------|
| `network_mode: host` | **CRITICAL** | Removes network isolation |
| No TLS/HTTPS | **HIGH** | All traffic is unencrypted |
| CORS wildcard | **MEDIUM** | Allows any origin to access API |
| Admin API exposed | **MEDIUM** | Caddy admin on :2019 |

### 3.3 Image Security

| Issue | Severity | Description |
|-------|----------|-------------|
| No image signing | **MEDIUM** | Images not verified with Cosign |
| No SBOM generation | **LOW** | No software bill of materials |
| Base images not pinned | **MEDIUM** | Non-reproducible builds |
| Trivy scans don't fail pipeline | **LOW** | Vulnerabilities don't block deploy |

### 3.4 Container Security

| Issue | Severity | Description |
|-------|----------|-------------|
| Containers run as root | **HIGH** | Privilege escalation risk |
| No read-only filesystem | **MEDIUM** | Containers can modify themselves |
| No seccomp/apparmor profiles | **MEDIUM** | Default system call access |
| No capability dropping | **MEDIUM** | Suricata has NET_ADMIN but others don't need it |

---

## 4. Monitoring & Observability

**Current State:**
- Health checks defined in CI/CD compose
- Basic logging configured
- No centralized logging (ELK/Loki)
- No metrics collection (Prometheus)
- No alerting configured

**Recommendations:**
1. Add Prometheus metrics endpoint to backend
2. Deploy Grafana for dashboards
3. Configure centralized logging with Loki or ELK
4. Add application performance monitoring (APM)

---

## 5. Backup & Disaster Recovery

**Current State:**
- SQLite database in volume
- No automated backups
- No documented restore procedure
- Email poller has backup script but main deployment doesn't

**Recommendations:**
1. Implement automated database backups
2. Document restore procedures
3. Test backup/restore regularly
4. Consider using PostgreSQL for production (gx10 compose has it but main doesn't)

---

## 6. Scalability & High Availability

**Current State:**
- Single instance deployment
- No load balancing
- No auto-scaling
- SQLite limits concurrent access

**Recommendations:**
1. Use PostgreSQL for multi-instance deployments
2. Add Redis for caching and session management
3. Implement horizontal pod autoscaling (if moving to K8s)
4. Consider using Caddy for load balancing multiple backends

---

## 7. Configuration Drift

**Multiple competing configurations found:**

| File | Python Version | Database | Network Mode |
|------|---------------|----------|--------------|
| `/docker-compose.yml` | - | SQLite | host |
| `/docker-compose.cicd.yml` | - | SQLite | host |
| `/docker-compose.yml.bak` | - | - | bridge |
| `/projects/vigil-home/poc-backend/docker-compose.yml` | 3.12 | SQLite | bridge |
| `/projects/vigil-home/deployment/gx10/docker-compose.gx10.yml` | - | PostgreSQL | mixed |

**This is a maintenance nightmare. Standardize on one approach.**

---

## Summary of Critical Issues

1. **EXPOSED CREDENTIALS** in `poc-backend/docker-compose.yml` (Gmail password)
2. **`network_mode: host`** removes network isolation
3. **No TLS/HTTPS** for any endpoints
4. **Containers run as root**
5. **Health check typos** in backup compose file (invalid ports)
6. **Configuration drift** across multiple compose files
7. **`StrictHostKeyChecking=no`** in SSH configurations

---

## Positive Findings

1. ✅ CI/CD pipeline is well-structured with security scanning
2. ✅ Multi-arch image builds (amd64 + arm64)
3. ✅ Automated rollback on deployment failure
4. ✅ Resource limits configured on containers
5. ✅ Health checks implemented (CI/CD compose)
6. ✅ Image caching for faster builds
7. ✅ Deployment scripts have good error handling
8. ✅ `unless-stopped` restart policy used

---

## Immediate Actions Required

1. **ROTATE EXPOSED CREDENTIALS** - Gmail app password compromised
2. **Remove `network_mode: host`** - Replace with proper Docker networking
3. **Standardize compose files** - Consolidate to single approach
4. **Enable TLS** - Use Caddy's automatic HTTPS or provide certificates
5. **Run containers as non-root** - Add USER directives to Dockerfiles

---

*Review completed by DevOps Infrastructure Reviewer Agent*  
*Date: 2026-05-26*
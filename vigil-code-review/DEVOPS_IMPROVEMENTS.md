# Vigil Dashboard - DevOps Improvements

**Priority-ranked recommendations for infrastructure hardening and operational excellence.**

---

## 🔴 CRITICAL - Do First (Security & Reliability)

### 1. Rotate Exposed Credentials
**Impact:** Prevents account takeover and unauthorized access  
**Effort:** 1 hour  
**Priority:** P0

The Gmail App Password in `projects/vigil-home/poc-backend/docker-compose.yml` is exposed in the repository.

**Actions:**
1. Immediately revoke the Gmail App Password at https://myaccount.google.com/security
2. Generate a new App Password
3. Move credentials to environment variables:
   ```yaml
   environment:
     - GMAIL_APP_PASSWORD=${GMAIL_APP_PASSWORD}
     - GMAIL_USER=${GMAIL_USER}
   ```
4. Add `.env` files to `.gitignore`
5. Clean git history with BFG Repo-Cleaner or git-filter-branch

---

### 2. Remove `network_mode: host`
**Impact:** Restores network isolation, reduces attack surface  
**Effort:** 2 hours  
**Priority:** P0

Host network mode removes Docker's security boundary.

**Actions:**
1. Update `docker-compose.yml`:
   ```yaml
   services:
     backend:
       # Remove: network_mode: host
       ports:
         - "8000:8000"
       networks:
         - vigil-net
     
     dashboard:
       # Remove: network_mode: host
       ports:
         - "8085:8085"
       networks:
         - vigil-net
   
   networks:
     vigil-net:
       driver: bridge
   ```
2. Update `docker-compose.cicd.yml` similarly
3. Test ARP scanning functionality still works (may need `cap_add: - NET_RAW`)

---

### 3. Fix Health Check Typos
**Impact:** Prevents false-negative health checks  
**Effort:** 15 minutes  
**Priority:** P1

**Actions:**
1. In `docker-compose.yml.bak`, fix line 20: `808000` → `8000`
2. In `docker-compose.yml.bak`, fix line 46: `808080` → `8080`
3. Consider deleting this backup file if not needed

---

## 🟠 HIGH - Security Hardening

### 4. Run Containers as Non-Root
**Impact:** Prevents privilege escalation if container is compromised  
**Effort:** 2 hours  
**Priority:** P1

**Backend Dockerfile:**
```dockerfile
# Add before final CMD
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
```

**Dashboard Dockerfile:**
```dockerfile
# Before final CMD
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx
USER nginx
```

---

### 5. Implement TLS/HTTPS
**Impact:** Encrypts all traffic, protects against sniffing  
**Effort:** 3 hours  
**Priority:** P1

**Option A - Caddy (Automatic HTTPS):**
```caddyfile
# Caddyfile
vigil.example.com {
    reverse_proxy backend:8000
}

dashboard.vigil.example.com {
    reverse_proxy dashboard:8085
}
```

**Option B - Use Tailscale certificates (already mounted in backup compose):**
Leverage existing Tailscale setup for internal TLS.

---

### 6. Secure SSH Configuration in CI/CD
**Impact:** Prevents MITM attacks during deployment  
**Effort:** 1 hour  
**Priority:** P1

**Actions:**
1. Generate known_hosts for GX-10:
   ```bash
   ssh-keyscan -H 192.168.50.30 >> known_hosts
   ```
2. Store in GitHub secret: `GX10_KNOWN_HOSTS`
3. Update workflow:
   ```yaml
   - name: Setup SSH
     run: |
       mkdir -p ~/.ssh
       echo "${{ secrets.GX10_SSH_KEY }}" > ~/.ssh/deploy_key
       echo "${{ secrets.GX10_KNOWN_HOSTS }}" > ~/.ssh/known_hosts
       chmod 600 ~/.ssh/deploy_key
       # Remove StrictHostKeyChecking=no and UserKnownHostsFile=/dev/null
   ```

---

## 🟡 MEDIUM - Best Practices

### 7. Pin Base Images to Digests
**Impact:** Reproducible builds, prevents unexpected changes  
**Effort:** 30 minutes  
**Priority:** P2

**Actions:**
```dockerfile
# Before:
FROM python:3.11-slim

# After:
FROM python:3.11-slim@sha256:1234abcd...
```

Get digest with: `docker pull python:3.11-slim && docker images --digests`

---

### 8. Use Docker Secrets or Environment Variables
**Impact:** Removes all hardcoded credentials  
**Effort:** 4 hours  
**Priority:** P2

**Actions:**
1. Create `.env.example` with dummy values
2. Add `.env` to `.gitignore`
3. Update all compose files to use `${VAR_NAME}`
4. For production, consider Docker Swarm secrets:
   ```yaml
   secrets:
     - db_password
   ```

---

### 9. Pin GitHub Actions to SHA
**Impact:** Prevents supply chain attacks via compromised actions  
**Effort:** 1 hour  
**Priority:** P2

**Actions:**
```yaml
# Before:
uses: aquasecurity/trivy-action@master

# After:
uses: aquasecurity/trivy-action@0.29.0
# Or better:
uses: aquasecurity/trivy-action@1234567...  # full commit SHA
```

---

### 10. Standardize Docker Compose Configuration
**Impact:** Reduces maintenance burden, prevents confusion  
**Effort:** 4 hours  
**Priority:** P2

**Current State:** 5+ compose files with different configurations

**Recommended Structure:**
```
docker/
├── docker-compose.yml          # Local development
├── docker-compose.prod.yml     # Production overrides
├── docker-compose.cicd.yml     # CI/CD specific
└── docker-compose.override.yml # Local overrides (gitignored)
```

**Actions:**
1. Consolidate to single approach (prefer PostgreSQL for production)
2. Remove `docker-compose.yml.bak`
3. Move `projects/vigil-home/poc-backend/docker-compose.yml` to archive or migrate
4. Document which compose file to use in which scenario

---

## 🟢 LOW - Nice to Have

### 11. Add Container Security Scanning to Pipeline
**Impact:** Catches vulnerabilities before deployment  
**Effort:** 2 hours  
**Priority:** P3

**Actions:**
```yaml
- name: Scan Docker images
  uses: aquasecurity/trivy-action@0.29.0
  with:
    image-ref: 'ghcr.io/${{ env.REPO_OWNER }}/${{ env.REPO_NAME }}-backend:${{ steps.sha.outputs.short_sha }}'
    format: 'sarif'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
```

Consider making the pipeline fail on HIGH severity after triage.

---

### 12. Implement Image Signing with Cosign
**Impact:** Supply chain security, image verification  
**Effort:** 3 hours  
**Priority:** P3

**Actions:**
```yaml
- name: Sign image with Cosign
  uses: sigstore/cosign-installer@3.3.0
- run: |
    cosign sign --yes ghcr.io/${{ env.REPO_OWNER }}/${{ env.REPO_NAME }}-backend@${{ steps.build.outputs.digest }}
```

---

### 13. Add Monitoring and Observability
**Impact:** Faster incident response, better visibility  
**Effort:** 8 hours  
**Priority:** P3

**Components:**
- Prometheus for metrics collection
- Grafana for dashboards
- Loki for log aggregation
- AlertManager for notifications

**Backend changes:**
```python
# Add to requirements.txt
prometheus-client>=0.19.0

# Add to main.py
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('vigil_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('vigil_request_latency_seconds', 'Request latency')
```

---

### 14. Implement Automated Backups
**Impact:** Data protection, disaster recovery  
**Effort:** 4 hours  
**Priority:** P3

**Actions:**
```yaml
# Add to docker-compose
services:
  backup:
    image: offen/docker-volume-backup:v2
    volumes:
      - vigil-data:/backup/data:ro
      - /var/backups/vigil:/archive
    environment:
      - BACKUP_CRON_EXPRESSION=0 2 * * *
      - BACKUP_RETENTION_DAYS=30
```

---

### 15. Add .dockerignore Files
**Impact:** Smaller images, faster builds, no secret leakage  
**Effort:** 30 minutes  
**Priority:** P3

**backend/.dockerignore:**
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.db
*.log
.git/
.gitignore
README.md
.env
.venv/
venv/
```

**dashboard/.dockerignore:**
```
node_modules/
.git/
.env
.env.local
README.md
build/
# Note: build/ should NOT be ignored if using pre-built files
```

---

## 📊 Priority Matrix

| Improvement | Impact | Effort | Priority | Owner |
|---------------|--------|--------|----------|-------|
| Rotate Exposed Credentials | Critical | 1h | P0 | Security |
| Remove network_mode: host | High | 2h | P0 | Infrastructure |
| Fix Health Check Typos | Medium | 15m | P1 | Reliability |
| Run Containers as Non-Root | High | 2h | P1 | Security |
| Implement TLS/HTTPS | High | 3h | P1 | Security |
| Secure SSH in CI/CD | High | 1h | P1 | Security |
| Pin Base Images | Medium | 30m | P2 | Reliability |
| Use Docker Secrets | Medium | 4h | P2 | Security |
| Pin GitHub Actions | Medium | 1h | P2 | Security |
| Standardize Compose Files | Medium | 4h | P2 | Maintainability |
| Container Security Scanning | Medium | 2h | P3 | Security |
| Image Signing (Cosign) | Medium | 3h | P3 | Security |
| Add Monitoring | High | 8h | P3 | Observability |
| Automated Backups | Medium | 4h | P3 | Reliability |
| Add .dockerignore | Low | 30m | P3 | Quality |

---

## 🎯 Implementation Roadmap

### Week 1: Critical Security
- [ ] Rotate exposed Gmail credentials
- [ ] Remove `network_mode: host` from all compose files
- [ ] Fix health check typos
- [ ] Run containers as non-root

### Week 2: Security Hardening
- [ ] Implement TLS/HTTPS with Caddy
- [ ] Secure SSH configuration in CI/CD
- [ ] Use Docker secrets for all credentials

### Week 3: Reliability & Standards
- [ ] Pin base images to digests
- [ ] Pin GitHub Actions to SHA
- [ ] Standardize compose file structure
- [ ] Add .dockerignore files

### Week 4: Observability & Automation
- [ ] Add Prometheus metrics
- [ ] Set up Grafana dashboards
- [ ] Implement automated backups
- [ ] Add container security scanning

---

## 💡 Additional Recommendations

### Consider Kubernetes
For future scalability, consider migrating to Kubernetes:
- Helm charts for configuration management
- Sealed Secrets for credential management
- cert-manager for automatic TLS
- Prometheus Operator for monitoring

### Implement GitOps
- Use Flux or ArgoCD for declarative deployments
- Store configurations in Git
- Automated drift detection and remediation

### Database Migration
- SQLite is fine for single-node but consider PostgreSQL for:
  - Concurrent access
  - Better backup options
  - Read replicas for scale

---

*Prioritized by impact vs effort. P0 items are blockers for production deployment.*

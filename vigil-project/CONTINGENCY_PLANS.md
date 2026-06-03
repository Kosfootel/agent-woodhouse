# Vigil Dashboard - Contingency Plans

**Project:** Vigil Dashboard Security Monitoring System  
**Version:** 1.0  
**Date:** 2026-05-26  
**Status:** 🔴 CRITICAL - CONTINGENCY PLANNING REQUIRED

---

## Executive Summary

This document provides detailed contingency plans for high-impact "what-if" scenarios that could derail the Vigil Dashboard project. Each scenario includes triggers, immediate response actions, fallback strategies, and recovery procedures.

**Key Scenarios Covered:**
1. GX-10 SSH remains broken
2. Database migration fails
3. Test coverage target not met
4. Security vulnerability discovered post-deployment
5. Team member becomes unavailable
6. Credential compromise detected
7. Third-party dependency compromised
8. Performance degradation in production

---

## Scenario 1: GX-10 SSH Remains Broken

### Trigger
- GitHub Actions deployment to GX-10 fails 3+ consecutive times
- SSH connection timeout or authentication failure
- `StrictHostKeyChecking=no` workaround ineffective

### Root Causes
- SSH key rotation without updating GitHub Secrets
- GX-10 IP address changed
- Firewall rules blocking GitHub Actions IP ranges
- SSH daemon configuration issue on GX-10

### Immediate Response (0-30 minutes)

```bash
# 1. Verify SSH connectivity from local machine
ssh -v -i ~/.ssh/gx10_deploy_key user@gx10.example.com

# 2. Check GitHub Actions runner IP ranges
# https://api.github.com/meta (actions key)

# 3. Test SSH from GitHub Actions debug workflow
```

### Fallback Strategies

#### Option A: Manual Deployment (Short-term)
```bash
# Local deployment script as temporary workaround
#!/bin/bash
set -e

echo "Deploying manually to GX-10..."
rsync -avz --progress ./build/ gx10:/opt/vigil-dashboard/
ssh gx10 "cd /opt/vigil-dashboard && docker-compose up -d"
echo "Deployment complete"
```

#### Option B: Alternative Deployment Target
- Deploy to staging server first
- Use existing staging environment as temporary production
- Communicate temporary URL to users

#### Option C: GitHub Actions Self-Hosted Runner
- Set up self-hosted runner on GX-10
- Eliminates network/firewall issues
- Requires runner maintenance overhead

### Recovery Procedures

1. **Fix SSH Issue:**
   - Rotate SSH keys properly
   - Update known_hosts in deployment workflow
   - Verify firewall rules allow GitHub IP ranges

2. **Implement Health Checks:**
   ```yaml
   # Add to workflow
   - name: Verify deployment
     run: |
       sleep 10
       curl -f http://gx10:8085/health || exit 1
   ```

3. **Document Fix:**
   - Add to deployment runbook
   - Update troubleshooting guide

### Decision Matrix

| Option | Effort | Risk | Recommendation |
|--------|--------|------|----------------|
| Manual Deploy | Low | Medium | **Immediate** (0-2 days) |
| Staging Fallback | Medium | Low | **Short-term** (2-7 days) |
| Self-hosted Runner | High | Low | **Long-term** (1-2 weeks) |

---

## Scenario 2: Database Migration Fails

### Trigger
- Alembic migration fails during deployment
- Data integrity check fails post-migration
- Foreign key constraint violations
- Rollback required

### Immediate Response (0-15 minutes)

```bash
# 1. Immediate rollback
docker-compose down
# Restore from backup
docker-compose up -d db
docker exec vigil-db psql -U vigil -d vigil -f /backups/pre-migration.sql

# 2. Verify data integrity
docker exec vigil-db psql -U vigil -c "SELECT COUNT(*) FROM devices;"
```

### Prevention Measures

```python
# Always backup before migration
# In deployment script:
def pre_migration_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/backups/vigil_{timestamp}.sql"
    subprocess.run([
        "pg_dump", "-h", "db", "-U", "vigil", 
        "-f", backup_file, "vigil"
    ])
    return backup_file
```

### Fallback Strategies

#### Option A: Staged Migration
```python
# Break migration into smaller steps
# migration/versions/001_add_indexes.py
# migration/versions/002_add_columns.py
# migration/versions/003_add_constraints.py
```

#### Option B: Blue-Green Deployment
- Keep old database running
- Migrate to new database instance
- Switch traffic only after verification
- Old database remains for instant rollback

#### Option C: Feature Flags
- Deploy schema changes as additive-only
- Use feature flags to control new features
- Gradual rollout with instant rollback capability

### Recovery Procedures

1. **Assessment:**
   ```sql
   -- Check migration status
   SELECT * FROM alembic_version;
   SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';
   ```

2. **Rollback:**
   ```bash
   # Alembic downgrade
   alembic downgrade -1
   ```

3. **Verification:**
   - Run data integrity checks
   - Verify application functionality
   - Monitor error rates

### Decision Matrix

| Option | Downtime | Data Risk | Recommendation |
|--------|----------|-----------|----------------|
| Direct Migration | Minutes | Medium | Dev only |
| Staged Migration | Minutes | Low | **Staging/Prod** |
| Blue-Green | None | Very Low | **Critical Prod** |

---

## Scenario 3: Test Coverage Target Not Met

### Trigger
- Sprint end approaching with < 50% coverage
- CI failing coverage gate
- Manual QA backlog growing

### Current State
- Frontend: 0% test coverage
- Backend: ~10% coverage (uses production DB)
- Target: 70% coverage

### Immediate Response

#### Critical Path Testing (Priority 1)
```javascript
// Test authentication flows first
describe('Authentication', () => {
  it('should login with valid credentials', () => {});
  it('should reject invalid credentials', () => {});
  it('should refresh token', () => {});
  it('should logout and invalidate token', () => {});
});

// Test device management
describe('Device Management', () => {
  it('should create device', () => {});
  it('should update device', () => {});
  it('should delete device', () => {});
});
```

### Fallback Strategies

#### Option A: Risk Acceptance with Compensating Controls
| Risk | Compensating Control | Owner |
|------|---------------------|-------|
| Untested auth | Manual security audit | Security Lead |
| Untested API | Contract testing | Backend Lead |
| Untested UI | Manual regression suite | QA Lead |
| No integration tests | Staged rollout | DevOps Lead |

**Documentation Required:**
```markdown
## Risk Acceptance: Test Coverage
- **Date:** 2026-05-26
- **Accepted By:** [Product Owner]
- **Risk:** Production defects, security vulnerabilities
- **Mitigation:** Manual QA, security audit, staged rollout
- **Review Date:** [30 days post-launch]
- **Conditions:** Must reach 70% coverage within 60 days
```

#### Option B: Delay Launch
- Extend timeline by 2-3 weeks
- Focus team on testing
- Defer non-critical features

#### Option C: External QA Support
- Contract QA firm for test writing
- Focus internal team on critical path
- Parallel testing effort

### Recovery Procedures

1. **Assessment:**
   - Identify untested critical paths
   - Calculate risk exposure
   - Document risk acceptance

2. **Compensating Controls:**
   - Increase manual QA cycles
   - Add production monitoring
   - Implement feature flags

3. **Post-Launch Plan:**
   - Week 1-2: Critical path tests
   - Week 3-4: Core feature tests
   - Week 5-8: Reach 70% coverage

### Decision Matrix

| Option | Timeline Impact | Risk Level | Recommendation |
|--------|-----------------|------------|----------------|
| Launch with Risk | None | High | With exec approval |
| Delay Launch | +2-3 weeks | Low | **Default** |
| External QA | +1 week cost | Medium | Budget permitting |

---

## Scenario 4: Security Vulnerability Discovered Post-Deployment

### Trigger
- Automated scan detects new CVE
- Penetration test findings
- Responsible disclosure received
- Anomalous activity detected

### Severity Classification

| Severity | Response Time | Actions |
|----------|---------------|---------|
| Critical (CVSS 9.0+) | Immediate | Incident response, potential takedown |
| High (CVSS 7.0-8.9) | 24 hours | Emergency patch, communication |
| Medium (CVSS 4.0-6.9) | 7 days | Scheduled fix |
| Low (CVSS 0.1-3.9) | Next release | Backlog item |

### Immediate Response (Critical Severity)

```yaml
# incident-response.yml
incident_response:
  t_plus_0:
    - Alert security team
    - Assess blast radius
    - Begin incident log
  
  t_plus_15_min:
    - Determine if takedown required
    - Notify stakeholders
    - Activate war room (if needed)
  
  t_plus_1_hour:
    - Develop hotfix strategy
    - Begin emergency patching
    - Prepare communications
  
  t_plus_4_hours:
    - Deploy hotfix to staging
    - Verify fix effectiveness
    - Coordinate production deployment
  
  t_plus_8_hours:
    - Deploy to production
    - Verify remediation
    - Post-incident review scheduled
```

### Fallback Strategies

#### Option A: Emergency Patch
```python
# Hotfix branch from current production
git checkout -b hotfix/SEC-XXX production
# Apply minimal fix
git commit -m "HOTFIX: [description]"
# Fast-track deployment
```

#### Option B: Feature Disable
```python
# If vulnerability in specific feature
@app.middleware("http")
async def disable_vulnerable_feature(request, call_next):
    if request.url.path == "/api/vulnerable-endpoint":
        return JSONResponse(
            {"error": "Feature temporarily disabled for security"},
            status_code=503
        )
    return await call_next(request)
```

#### Option C: Service Takedown
- If exploit is actively being used
- If data breach confirmed
- If fix cannot be deployed quickly

### Recovery Procedures

1. **Containment:**
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable additional logging

2. **Eradication:**
   - Deploy security patches
   - Remove malicious access
   - Verify clean state

3. **Recovery:**
   - Restore from known good backups
   - Verify service health
   - Resume normal operations

4. **Post-Incident:**
   - Document lessons learned
   - Update security procedures
   - Share relevant indicators

### Communication Templates

**Internal Security Alert:**
```
Subject: [CRITICAL] Security Incident - Immediate Action Required

Summary: [Brief description]
Severity: Critical (CVSS [X.X])
Impact: [Affected systems/data]
Actions Required:
1. [Action item]
2. [Action item]

Incident Commander: [Name]
War Room: [Link/Location]
Status Page: [Link]
```

---

## Scenario 5: Team Member Becomes Unavailable

### Trigger
- Extended illness
- Unexpected departure
- Unplanned leave

### Impact Assessment

| Role | Critical Knowledge | Backup | Cross-Training |
|------|-------------------|--------|----------------|
| Security Lead | Crypto, Auth | None | Needed |
| Backend Lead | DB Schema, APIs | None | Partial |
| Frontend Lead | Component architecture | None | Partial |
| DevOps Lead | Infrastructure, CI/CD | None | Partial |

### Immediate Response

#### Knowledge Transfer Checklist
- [ ] Repository access verified
- [ ] Documentation location known
- [ ] Credentials/passwords accessible
- [ ] Vendor contacts documented
- [ ] Deployment procedures documented
- [ ] Monitoring dashboards access

### Fallback Strategies

#### Option A: Redistribute Work
| Role | Can Cover | Cannot Cover |
|------|-----------|--------------|
| Backend Lead | Basic frontend | Security review |
| Frontend Lead | API changes | DB optimization |
| DevOps Lead | Basic deployments | Security hardening |

#### Option B: Contract Support
- Security: Security consultant ($200-300/hr)
- Backend: Python contractor ($150-200/hr)
- Frontend: React contractor ($120-180/hr)
- DevOps: DevOps contractor ($150-200/hr)

#### Option C: Scope Reduction
- Defer non-critical features
- Extend timeline proportionally
- Focus on core functionality

### Prevention Measures

1. **Documentation Requirements:**
   - Architecture Decision Records (ADRs)
   - Deployment runbooks
   - Security procedures
   - Incident response plans

2. **Cross-Training:**
   - Weekly knowledge sharing sessions
   - Pair programming
   - Rotation through critical tasks

3. **Bus Factor Improvement:**
   - Minimum 2 people per critical skill
   - Shared responsibility for critical components
   - Regular skill gap assessment

---

## Scenario 6: Credential Compromise Detected

### Trigger
- Suspicious login activity
- Credentials found in breach database
- Unauthorized access detected
- Phishing attack successful

### Immediate Response (0-30 minutes)

```bash
# 1. Immediate rotation
# Gmail
# - Change password immediately
# - Revoke all app passwords
# - Review security activity

# 2. Audit access
gcloud logging read "protoPayload.authenticationInfo.principalEmail" \
  --limit=100 --format="table(timestamp,resource.labels.method_name)"

# 3. Isolate affected systems
docker-compose down  # Stop services with exposed credentials
# Rotate all potentially exposed credentials
```

### Credential Rotation Checklist

- [ ] Gmail App Password (SEC-001)
- [ ] Database credentials
- [ ] JWT secrets
- [ ] API keys
- [ ] SSH keys
- [ ] Docker registry tokens
- [ ] Cloud provider credentials
- [ ] Third-party service tokens

### Recovery Procedures

1. **Assessment:**
   - Determine scope of compromise
   - Identify affected systems
   - Check for lateral movement

2. **Containment:**
   - Revoke all compromised credentials
   - Disable affected accounts
   - Block suspicious IP addresses

3. **Eradication:**
   - Remove attacker access
   - Patch exploited vulnerabilities
   - Scan for persistence mechanisms

4. **Recovery:**
   - Deploy new credentials
   - Verify system integrity
   - Resume operations

5. **Post-Incident:**
   - Root cause analysis
   - Process improvements
   - Security awareness training

---

## Scenario 7: Third-Party Dependency Compromised

### Trigger
- Dependency vulnerability disclosed
- Malicious package detected
- Supply chain attack reported

### Immediate Response

```bash
# 1. Audit dependencies
npm audit --audit-level=high
pip-audit --format=json

# 2. Check for known compromised packages
# https://security.snyk.io/
# https://github.com/advisories

# 3. Isolate if needed
# Pin to last known good version
npm install package@1.2.3 --save-exact
```

### Fallback Strategies

#### Option A: Pin to Safe Version
```json
{
  "dependencies": {
    "affected-package": "1.2.3"  // Last known good
  }
}
```

#### Option B: Alternative Package
Research alternative packages with similar functionality:
- Evaluate security track record
- Check maintenance status
- Review community adoption

#### Option C: Vendor Fork
- Fork compromised package
- Apply security patches
- Maintain until upstream fixed

### Prevention Measures

1. **Dependency Pinning:**
   - Use exact versions in production
   - Lock files (package-lock.json, requirements.txt --hash)

2. **Automated Scanning:**
   - Snyk integration in CI
   - Dependabot alerts
   - Daily vulnerability reports

3. **Vendor Assessment:**
   - Maintenance status check
   - Security disclosure process
   - Community health metrics

---

## Scenario 8: Performance Degradation in Production

### Trigger
- P95 latency > 500ms
- Error rate > 0.1%
- CPU/memory usage > 80%
- User complaints

### Immediate Response

```bash
# 1. Diagnose
# Check resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check logs
docker-compose logs --tail=100 backend | grep ERROR

# 2. Quick fixes
# Scale horizontally
docker-compose up --scale backend=3 -d

# Enable caching
# Restart with increased workers
```

### Performance Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| P95 Latency | > 200ms | > 500ms | Scale up |
| Error Rate | > 0.01% | > 0.1% | Rollback |
| CPU Usage | > 70% | > 90% | Scale out |
| Memory Usage | > 80% | > 95% | Restart/scale |
| DB Connections | > 80% | > 95% | Connection pool |

### Fallback Strategies

#### Option A: Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
```

#### Option B: Caching Layer
```python
# Add Redis caching for expensive queries
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.get("/api/devices")
@cache(expire=60)
async def get_devices():
    return await fetch_devices()
```

#### Option C: Database Optimization
- Add indexes
- Query optimization
- Connection pooling
- Read replicas

#### Option D: Circuit Breaker
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def external_api_call():
    return await fetch_external_data()
```

---

## Contingency Plan Summary

| Scenario | Trigger | Primary Response | Fallback |
|----------|---------|------------------|----------|
| GX-10 SSH Broken | 3 failed deploys | Manual deploy | Staging fallback |
| DB Migration Fail | Integrity check fail | Blue-green deploy | Rollback |
| Low Test Coverage | <50% at deadline | Delay launch | Risk acceptance |
| Security Vuln | CVSS 9.0+ found | Emergency patch | Feature disable |
| Team Unavailable | Key person out | Redistribute | Contract support |
| Credential Compromise | Suspicious activity | Rotate all | System isolation |
| Dependency Compromised | CVE disclosed | Pin version | Alternative pkg |
| Performance Issues | P95 > 500ms | Scale up | Optimize queries |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-26 | Risk Management Engineer | Initial contingency plans |

---

## Related Documents

- [RISK_REGISTER.md](RISK_REGISTER.md) - Risk inventory
- [RISK_MITIGATION_PLAN.md](RISK_MITIGATION_PLAN.md) - Mitigation strategies
- [SECURITY_RISKS.md](SECURITY_RISKS.md) - Security-specific analysis

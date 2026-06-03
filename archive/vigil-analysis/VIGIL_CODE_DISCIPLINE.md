# VIGIL Code Discipline Protocol
**Effective: 2026-05-24 19:15 EDT**
**Issued by: Woodhouse (on authority of Mr. Ross)**

## CRITICAL: Single Source of Truth

**GitHub repository `Kosfootel/agent-woodhouse` branch `hermes/vigil-playbooks-models`** is the ONLY authoritative source of code.

**NO EXCEPTIONS.**

---

## Workflow (Mandatory)

### Step 1: Declare Location
**Every task MUST start with:**
```
Working location: [local-path]
GitHub branch: hermes/vigil-playbooks-models
Target deployment: GX-10 (192.168.50.30)
```

### Step 2: Work Locally
Make changes in your assigned workspace.

### Step 3: Commit to Git
```bash
git add [files]
git commit -m "type: description"
```

### Step 4: Push to GitHub
```bash
git push origin hermes/vigil-playbooks-models
```

**VERIFY:** Check GitHub web interface that commit exists.

### Step 5: Deploy to GX-10
```bash
ssh erik-ross@192.168.50.30
cd ~/projects/vigil-home
git pull origin hermes/vigil-playbooks-models
```

### Step 6: Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

### Step 7: Verify
```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/[endpoint]
```

---

## Verification Checklist (Before Reporting Success)

- [ ] Commit exists on GitHub (visible in web interface)
- [ ] GX-10 has pulled the commit (`git log` shows it)
- [ ] Containers rebuilt and running
- [ ] Feature actually works (tested via curl or browser)
- [ ] Sir can see the change

**NO REPORTING SUCCESS WITHOUT VERIFICATION.**

---

## Subagent Requirements

**Every subagent task MUST:**

1. **Declare location** at start
2. **Commit to hermes/vigil-playbooks-models** (not main, not local branches)
3. **Push to GitHub** before any deployment
4. **Report commit hash** in completion
5. **Verify deployment** on GX-10

**Template:**
```
## Task Declaration
- Working: /Users/FOS_Erik/.openclaw/workspace
- Branch: hermes/vigil-playbooks-models
- Target: GX-10

## Completion Report
- Commit: [hash]
- GitHub: [link]
- GX-10: Pulled and rebuilt
- Verification: [test results]
```

---

## Audit Trail

**Current Status (2026-05-24):**
- Woodhouse workspace: on `main` branch (WRONG - should be hermes/vigil-playbooks-models)
- GX-10: Unknown state
- Subagents: Unknown branches/working locations

**Required Action:**
1. Switch Woodhouse to hermes/vigil-playbooks-models
2. Audit GX-10 code state
3. Reconcile differences
4. Establish branch as mandatory

---

## Enforcement

**Violations:**
- Working on wrong branch → STOP, switch branches
- Not pushing to GitHub → STOP, push first
- Direct changes on GX-10 → STOP, commit to Git first
- Reporting success without verification → INVALID

**This protocol is MANDATORY.**

---

*Protocol established by Woodhouse*
*2026-05-24*

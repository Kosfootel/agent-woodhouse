# Extrusion Supplies - Hosting & Deployment Guide

## Client Requirements

**Hosting Platform:** Hostinger (client-specified)  
**Source Control:** GitHub (client-specified)  
**Deployment Method:** GitHub Actions → Hostinger

---

## Why Hostinger + GitHub?

### Client Benefits

**Cost-Effective:**
- Hostinger: $3-15/month vs Vercel Pro $20/month
- GitHub: Free for public/private repos
- Total: ~$50-100/year vs $240/year+

**Client Control:**
- Client owns Hostinger account
- Client owns GitHub repository
- No vendor lock-in
- Easy to transfer/migrate later

**Industry Standard:**
- GitHub is #1 developer platform
- Hostinger is reliable, established
- Easy to find developers familiar with stack

---

## Recommended Hostinger Plan

### Option 1: Business Shared Hosting (Recommended)

**Price:** ~$3-5/month  
**Best for:** Static sites, small applications

**Features:**
- 100 GB SSD storage
- Free SSL certificate
- Free domain (1 year)
- CDN included
- Daily backups
- Git deployment ready
- SSH access

**Setup:**
1. Sign up at hostinger.com
2. Choose "Business Shared Hosting"
3. Select domain: extrusionsupplies.com
4. Enable SSL and CDN

### Option 2: Cloud Startup (For Growth)

**Price:** ~$8-10/month  
**Best for:** Higher traffic, API needs

**Features:**
- 200 GB NVMe storage
- 2 GB RAM
- 2 CPU cores
- Free SSL + domain
- Dedicated IP
- Full root access
- Node.js support

**Choose if:**
- Expecting 10k+ visitors/month
- Need server-side processing
- Want more control

---

## GitHub Repository Structure

```
extrusion-supplies/
├── .github/
│   └── workflows/
│       ├── deploy.yml          # Main deployment workflow
│       └── test.yml            # Pull request testing
├── src/
│   ├── app/                    # Next.js App Router
│   ├── components/
│   ├── lib/
│   └── types/
├── sanity/                     # Sanity Studio
│   ├── schemas/
│   └── sanity.config.ts
├── public/                     # Static assets
├── .env.example               # Environment template
├── .env.local                 # Local secrets (gitignored!)
├── .gitignore
├── next.config.js             # Configured for static export
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```

---

## GitHub Actions Deployment

### 1. Create Deployment Workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to Hostinger

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run linting
      run: npm run lint
      
    - name: Run tests
      run: npm test
      
    - name: Build Next.js app
      run: npm run build
      env:
        NEXT_PUBLIC_SANITY_PROJECT_ID: ${{ secrets.SANITY_PROJECT_ID }}
        NEXT_PUBLIC_SANITY_DATASET: ${{ secrets.SANITY_DATASET }}

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Build Next.js app
      run: npm run build
      env:
        NEXT_PUBLIC_SANITY_PROJECT_ID: ${{ secrets.SANITY_PROJECT_ID }}
        NEXT_PUBLIC_SANITY_DATASET: ${{ secrets.SANITY_DATASET }}
        SANITY_API_TOKEN: ${{ secrets.SANITY_API_TOKEN }}
        
    - name: Export static site
      run: npm run export
      
    - name: Deploy to Hostinger via FTP
      uses: SamKirkland/FTP-Deploy-Action@v4.3.4
      with:
        server: ${{ secrets.HOSTINGER_FTP_SERVER }}
        username: ${{ secrets.HOSTINGER_FTP_USERNAME }}
        password: ${{ secrets.HOSTINGER_FTP_PASSWORD }}
        local-dir: ./out/
        server-dir: /public_html/
        dangerous-clean-slate: false
```

### 2. Add GitHub Secrets

**Go to:** GitHub Repo → Settings → Secrets → Actions

Add these secrets:

| Secret Name | Value | From |
|-------------|-------|------|
| `SANITY_PROJECT_ID` | abc123xyz | Sanity dashboard |
| `SANITY_DATASET` | production | Sanity dashboard |
| `SANITY_API_TOKEN` | sk-... | Sanity dashboard |
| `HOSTINGER_FTP_SERVER` | ftp.extrusionsupplies.com | Hostinger panel |
| `HOSTINGER_FTP_USERNAME` | u123456789 | Hostinger panel |
| `HOSTINGER_FTP_PASSWORD` | •••••••• | Hostinger panel |

### 3. Next.js Configuration

**File:** `next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for Hostinger
  output: 'export',
  distDir: 'out',
  
  // Image optimization for static export
  images: {
    unoptimized: true,
  },
  
  // Clean URLs with trailing slash
  trailingSlash: true,
  
  // Environment variables available at build time
  env: {
    NEXT_PUBLIC_SANITY_PROJECT_ID: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID,
    NEXT_PUBLIC_SANITY_DATASET: process.env.NEXT_PUBLIC_SANITY_DATASET,
  },
}

module.exports = nextConfig
```

---

## Deployment Workflow

### For Developers

```bash
# 1. Make changes locally
npm run dev  # Test locally

# 2. Commit changes
git add .
git commit -m "Update hero carousel"

# 3. Push to main
git push origin main

# 4. GitHub Actions automatically:
#    - Runs tests
#    - Builds application
#    - Exports static HTML
#    - Deploys to Hostinger
#    - (Takes ~3-5 minutes)
```

### Monitoring Deployment

**Check status:**
1. Go to GitHub repository
2. Click "Actions" tab
3. See deployment status
4. Green checkmark = success
5. Red X = failure (check logs)

---

## Sanity CMS Hosting

**Important:** Sanity CMS is separate from website hosting

### Sanity Configuration

**Sanity Studio URL:** `https://[project-id].sanity.studio`

**Client Access:**
- Tom logs into Sanity Studio (separate from website)
- Edits content in Sanity
- Changes appear on website automatically
- No need to touch GitHub or Hostinger

**Why separate?**
- ✅ CMS works independently
- ✅ No server maintenance for CMS
- ✅ Automatic backups
- ✅ Real-time collaboration
- ✅ Works on iPhone and Desktop

---

## Domain Configuration

### Step 1: Transfer Domain (if needed)

**Option A:** Keep domain at current registrar
- Update DNS A record to Hostinger IP
- Keep domain management where it is

**Option B:** Transfer to Hostinger
- Unlock domain at current registrar
- Get EPP code
- Initiate transfer in Hostinger
- Wait 5-7 days

### Step 2: DNS Configuration

**In Hostinger hPanel:**

1. Go to Domains → DNS Zone Editor
2. Add records:

```
Type: A
Name: @
Points to: [Hostinger Server IP]
TTL: 14400

Type: CNAME
Name: www
Points to: extrusionsupplies.com
TTL: 14400
```

### Step 3: SSL Certificate

**In Hostinger hPanel:**

1. Go to Advanced → SSL
2. Click "Install SSL"
3. Select domain
4. AutoSSL (Let's Encrypt) - FREE
5. Wait for installation (5-30 minutes)

---

## Cost Breakdown

### Year 1 Costs

| Item | Monthly | Yearly |
|------|---------|--------|
| Hostinger Business | $3.99 | $47.88 |
| Sanity (free tier) | $0 | $0 |
| GitHub (free) | $0 | $0 |
| Domain (Hostinger) | - | $0 (included) |
| **Total Year 1** | - | **~$48** |

### Ongoing Costs (Year 2+)

| Item | Yearly |
|------|--------|
| Hostinger renewal | ~$96 |
| Domain renewal | ~$15 |
| Sanity (free tier) | $0 |
| **Total Year 2+** | **~$111/year** |

**Compare to Wix:**
- Wix Business: ~$276/year
- **Savings: ~$165/year**

---

## Backup Strategy

### Automatic Backups

**Hostinger:**
- Daily backups included
- 7 days retention
- Can restore from hPanel

**GitHub:**
- Complete version history
- Can rollback to any commit
- Branch protection rules

**Sanity:**
- Automatic daily backups
- 30 days retention
- Export available anytime

### Manual Backup Process

```bash
# Backup Sanity content
sanity dataset export production production-backup.tar.gz

# Backup GitHub repo
git clone --mirror https://github.com/user/repo.git

# Hostinger backup
# Use hPanel backup tool
```

---

## Troubleshooting

### Deployment Failed

**Check:**
1. GitHub Actions logs (Actions tab → Failed build)
2. Environment variables set correctly
3. Build passes locally (`npm run build`)
4. FTP credentials correct

### Site Not Updating

**Check:**
1. Browser cache (hard refresh: Ctrl+F5)
2. CDN cache (purge in Hostinger)
3. Deployment completed successfully
4. Correct branch deployed (main)

### SSL Issues

**Check:**
1. SSL installed in hPanel
2. HTTPS redirect enabled
3. Mixed content (HTTP images)
4. Certificate not expired

---

## Security Best Practices

### GitHub Repository

```
✅ Make repository private (recommended)
✅ Enable branch protection on main
✅ Require PR reviews before merge
✅ Enable Dependabot alerts
✅ Use secrets for all sensitive data
```

### Hostinger Security

```
✅ Keep PHP/Node versions updated
✅ Enable 2FA on Hostinger account
✅ Use strong FTP password
✅ Enable hotlink protection
✅ Configure firewall rules
```

### Sanity Security

```
✅ Use tokens, not credentials
✅ Set CORS origins
✅ Enable 2FA for studio login
✅ Review access logs
✅ Rotate tokens periodically
```

---

## Migration Checklist

### Pre-Migration

- [ ] GitHub repository created
- [ ] Hostinger account set up
- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Environment variables in GitHub Secrets
- [ ] GitHub Actions workflow tested
- [ ] Deployment pipeline working

### Migration Day

- [ ] Final content export from Wix
- [ ] Content imported to Sanity
- [ ] Images uploaded to Sanity
- [ ] DNS switched to Hostinger
- [ ] 301 redirects configured
- [ ] Site tested on Hostinger
- [ ] Sitemap submitted to Google

### Post-Migration

- [ ] Monitor for 404 errors
- [ ] Verify analytics tracking
- [ ] Test contact forms
- [ ] Check mobile responsiveness
- [ ] Confirm SSL working
- [ ] Train Tom on new CMS

---

## Support Resources

**Hostinger:**
- 24/7 Live Chat
- Knowledge Base
- Video Tutorials

**GitHub:**
- Documentation: docs.github.com
- Community: github.community
- Status: status.github.com

**Sanity:**
- Documentation: sanity.io/docs
- Slack Community
- Support: sanity.io/contact

**Next.js:**
- Documentation: nextjs.org/docs
- GitHub Discussions

---

## Summary

**Infrastructure:**
- 🏠 **Hostinger:** Website hosting ($48/year)
- 💻 **GitHub:** Source control + CI/CD (free)
- 🎨 **Sanity:** Content management (free tier)
- 🔒 **SSL:** Free Let's Encrypt
- 🚀 **CDN:** Included with Hostinger

**Total Cost:** ~$48/year (Year 1), ~$111/year ongoing

**Client Benefits:**
- ✅ Cost-effective vs Wix
- ✅ Full ownership (hosting, code, domain)
- ✅ Industry standard tools
- ✅ Automatic deployments
- ✅ Easy to maintain and extend

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
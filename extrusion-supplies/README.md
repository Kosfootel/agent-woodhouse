# Extrusion Supplies Website Replacement Project

## Overview

This repository contains the requirements, design documentation, and implementation guidance for replacing the current Wix-based website at https://extrusionsupplies.com with a custom-built solution that maintains ease of use for the client while improving performance, SEO, and maintainability.

## Client Profile

**Business:** Extrusion Supplies  
**Owner:** Tom Nentwick  
**Industry:** B2B Aluminum Extrusion Equipment Broker  
**Location:** Canfield, OH, USA  
**Tech Level:** Novice - requires simple WYSIWYG editing tools

## Current Site Analysis

See `docs/current-site-review.md` for the complete analysis of the existing Wix website.

## Project Goals

1. **Preserve existing functionality** while improving performance and SEO
2. **Enable easy content management** without technical knowledge
3. **Maintain visual identity** and brand consistency
4. **Improve search visibility** through better SEO implementation
5. **Reduce ongoing costs** compared to Wix subscription model

## Repository Structure

```
bettermachine/extrusion-supplies/
├── README.md
├── PROJECT-SUMMARY.md
├── docs/
│   ├── current-site-review.md
│   ├── requirements.md
│   ├── cms-mobile-requirements.md
│   ├── hosting-deployment.md      ← NEW: Hostinger + GitHub setup
│   ├── design-system.md
│   ├── content-model.md
│   ├── seo-strategy.md
│   └── migration-plan.md
├── prompts/
│   ├── design-prompt.md
│   ├── implementation-prompt.md
│   └── deployment-prompt.md
└── assets/
    └── (reference images and exports)
```

## Quick Links

- [Requirements](docs/requirements.md) - Complete functional and non-functional requirements
- [CMS Mobile Requirements](docs/cms-mobile-requirements.md) - iPhone + Windows editing specifications
- [Hosting & Deployment](docs/hosting-deployment.md) - Hostinger + GitHub integration guide
- [Design System](docs/design-system.md) - Visual design guidelines and components
- [Content Model](docs/content-model.md) - CMS structure and data schema
- [SEO Strategy](docs/seo-strategy.md) - Search optimization recommendations
- [Migration Plan](docs/migration-plan.md) - Steps for transitioning from Wix

## Client Requirements

**Content Management:**
- WYSIWYG editing for homepage images and products
- Cross-platform: Windows Desktop AND iPhone with equal functionality
- Camera upload from iPhone

**Hosting & Infrastructure:**
- **Hosting Platform:** Hostinger (client preference)
- **Source Control:** GitHub integration
- **CMS:** Sanity (headless, cross-platform compatible)

**Site Purpose:**
- Product catalog browsing (B2B, no e-commerce transactions)
- SEO-optimized for industrial equipment buyers
- Fast, mobile-responsive design

---

## Tech Stack (Client-Specified)

Based on client requirements:

| Component | Selection | Rationale |
|-----------|-----------|-----------|
| **Frontend** | Next.js 14 | SEO-friendly, fast, modern |
| **CMS** | Sanity | Cross-platform editing, iPhone compatible |
| **Hosting** | **Hostinger** | Client preference, cost-effective |
| **Source Control** | **GitHub** | Client requirement, industry standard |
| **Database** | Sanity (hosted) | No server management needed |
| **CI/CD** | GitHub Actions → Hostinger | Automated deployments |

### Hosting: Hostinger Setup

**Recommended Hostinger Plan:**
- **Business Shared Hosting** or **Cloud Startup**
- Supports Node.js (for Next.js static export or full-stack)
- Free SSL certificate
- CDN included
- Git deployment support

**Deployment Strategy:**
```
GitHub Repo → GitHub Actions Build → Hostinger Deploy
     ↑                                              ↓
Developer pushes                          Live Website
```

**Why Hostinger Works:**
- ✅ Cost-effective (client preference)
- ✅ Node.js support for Next.js
- ✅ Git integration available
- ✅ Free SSL + CDN
- ✅ 99.9% uptime guarantee

### Source Control: GitHub Integration

**Repository Structure:**
```
extrusion-supplies/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions deployment
├── src/                         # Next.js application
├── sanity/                      # Sanity schemas
├── public/                      # Static assets
├── .env.example                 # Environment variables template
├── next.config.js
└── package.json
```

**GitHub Actions Workflow:**
- Build on every push to main branch
- Run tests and linting
- Deploy to Hostinger automatically
- Notify on success/failure

---

## Tech Stack Recommendation

Based on client needs (WYSIWYG editing, no-code content management, **cross-platform editing on Windows and iPhone**), we recommend:

### CMS Platform Selection Criteria

**Critical Requirement:** The CMS must work equally well on **Windows Desktop** and **iPhone**, with full editing capabilities on both platforms.

**Client's Preferred Tools:**
- Windows Desktop (Chrome, Edge, Firefox)
- iPhone (Safari, Chrome iOS)

**Required Capabilities:**
- Upload images from iPhone camera or photo library
- Edit products, homepage, and pages from either device
- Touch-optimized interface for mobile
- No desktop-only features

See `docs/cms-mobile-requirements.md` for detailed cross-platform specifications.

---

### Recommended Stack: Next.js + Sanity + Hostinger + GitHub

**Why this stack meets all requirements:**

**Sanity CMS:**
- ✅ **Responsive Studio** - Works on Windows, iPhone, and all devices
- ✅ **Camera Integration** - Upload directly from iPhone camera or library
- ✅ **Touch-Friendly** - 44px+ touch targets, no hover dependencies
- ✅ **No App Install** - Web-based, works in Safari/Chrome on iPhone
- ✅ **Full Feature Parity** - Every feature works on both platforms

**Hostinger Hosting:**
- ✅ **Client Preference** - Specified by client
- ✅ **Cost-Effective** - Affordable hosting plans
- ✅ **Node.js Support** - Can run Next.js applications
- ✅ **Git Integration** - Deploy from GitHub
- ✅ **Free SSL + CDN** - Included in plans

**GitHub Source Control:**
- ✅ **Client Requirement** - Specified by client
- ✅ **Industry Standard** - Best practices for development
- ✅ **CI/CD Integration** - Automated deployments
- ✅ **Version History** - Complete change tracking
- ✅ **Collaboration** - Easy team collaboration

**Next.js Frontend:**
- ✅ **SEO Excellence** - Server-side rendering for search engines
- ✅ **Performance** - Fast page loads, Core Web Vitals optimized
- ✅ **Flexibility** - Static export or full-stack deployment
- ✅ **Modern** - React-based, industry-leading framework

---

### Alternative CMS Comparison

| CMS | Windows | iPhone | Camera Upload | Best For |
|-----|---------|--------|---------------|----------|
| **Sanity** | ✅ Full | ✅ Full | ✅ Native | **This Project** |
| WordPress | ✅ Full | ⚠️ Limited | ⚠️ Plugin | Familiarity over mobile |
| Decap | ✅ Full | ❌ Poor | ❌ No | Git-based workflows |
| Contentful | ✅ Full | ✅ Full | ✅ Yes | Enterprise complexity |

---

## Next Steps

1. Review requirements with client
2. Confirm tech stack choice
3. Create design mockups
4. Develop MVP
5. Migrate content
6. Launch and SEO optimization

---

*Last Updated: 2026-05-30*  
*Agency: BetterMachine*
# Extrusion Supplies Website Project Summary

## Project Overview

**Client:** Extrusion Supplies (Tom Nentwick)  
**Current Platform:** Wix  
**Project Goal:** Replace Wix with a modern, fast, SEO-optimized website that Tom can easily manage
**Repository:** `bettermachine/extrusion-supplies`

---

## What Was Created

This repository contains complete documentation for rebuilding the Extrusion Supplies website:

### 📁 Repository Structure

```
bettermachine/extrusion-supplies/
├── README.md                          # Project overview and quick links
├── docs/
│   ├── current-site-review.md         # Analysis of existing Wix site
│   ├── requirements.md               # Complete functional requirements
│   ├── design-system.md              # Visual design guidelines
│   ├── content-model.md              # CMS data structure
│   ├── seo-strategy.md             # SEO recommendations
│   └── migration-plan.md             # Step-by-step migration guide
└── prompts/
    ├── design-prompt.md              # AI prompt for design phase
    └── implementation-prompt.md      # AI prompt for development phase
```

---

## Key Findings from Site Review

### Current Site Stats
- **Platform:** Wix Website Builder
- **Pages:** ~50 pages
- **Products:** ~100 individual product listings
- **Categories:** 20+ equipment categories
- **Languages:** English + Italian

### Strengths (Preserve)
1. Clear brand identity with 20+ years of experience
2. Comprehensive product catalog
3. Multiple featured brand partnerships
4. Personal touch with founder visibility
5. Good image assets with proper optimization
6. Clean URL structure
7. Mobile-responsive design

### Weaknesses (Fix)
1. ❌ No structured data (Schema.org)
2. ❌ Repetitive meta descriptions
3. ❌ No canonical tags
4. ❌ Wix platform limitations
5. ❌ Slow page load times (~3-4s)
6. ❌ Limited SEO control

---

## Recommended Tech Stack

### Client-Specified Infrastructure:
- **Frontend:** Next.js 14 (React framework)
- **CMS:** Sanity (cross-platform editing)
- **Hosting:** Hostinger (client preference)
- **Source Control:** GitHub (client requirement)
- **Deployment:** GitHub Actions → Hostinger

### Cost Comparison:
| Platform | Year 1 Cost | Notes |
|----------|-------------|-------|
| **New Stack** | ~$48 | Hostinger + Sanity (free) + GitHub (free) |
| **Wix** | ~$276 | Current platform |
| **Savings** | ~$228/year | 83% cost reduction |

---

## Client Requirements Summary

### Must Support (Non-negotiable)
1. **WYSIWYG Homepage Editing** - Change hero images, featured products easily
2. **Product Management** - Add, edit, hide products without technical help
3. **SEO Optimization** - Better than current Wix implementation
4. **Mobile-Responsive** - Works perfectly on all devices

### Nice to Have
- Multilingual support (Italian)
- Blog functionality
- Advanced product filtering
- Live chat integration

---

## Design Direction

### Visual Style
- **Feel:** Professional, industrial, trustworthy
- **Colors:** Dark grays (#1a1a1a), gold accent (#c9a227), clean white backgrounds
- **Typography:** Inter font family, clean and readable
- **Imagery:** Industrial equipment photography, slightly desaturated

### Key Pages
1. **Homepage** - Hero carousel, category grid, featured products, about section
2. **Product Listing** - Filterable grid with search
3. **Product Detail** - Image gallery, specs, contact CTA
4. **Contact** - Form + contact information
5. **About** - Tom's bio and company history

---

## SEO Strategy Highlights

### Immediate Wins
1. **Structured Data** - Implement Product, Organization, LocalBusiness schema
2. **Meta Tags** - Unique titles/descriptions per page
3. **URL Structure** - `/equipment/[category]/[product-slug]`
4. **Image Optimization** - WebP/AVIF with responsive sizes
5. **Core Web Vitals** - Target < 2.5s LCP

### Content Strategy
- 2-4 blog posts per month (equipment guides, industry news)
- FAQ page for common questions
- Expanded About page (500+ words)
- Customer case studies (when available)

---

## CMS Structure (Sanity)

### Content Types
1. **Product** - Equipment listings with images, specs, availability
2. **Category** - Equipment categories with hierarchy
3. **Page** - Static content pages (About, Contact, etc.)
4. **Homepage** - Singleton for homepage configuration
5. **Site Settings** - Global configuration

### For Tom's Daily Use
- Simple product creation form
- Image upload with preview
- Rich text editor for descriptions
- Status toggle (published/hidden/draft)
- Featured checkbox for homepage
- Homepage section editing

---

## Migration Plan Overview

### Timeline: 6-8 Weeks

**Week 1:** Discovery, audit, content export  
**Weeks 2-4:** Development (Next.js + Sanity setup, components, pages)  
**Week 5:** SEO implementation, CMS customization  
**Week 6:** Testing, UAT with Tom  
**Week 7:** Launch  
**Week 8:** Post-launch monitoring, training

### Critical Steps
1. Export all content from Wix
2. Create URL redirect mapping
3. Optimize and migrate all images
4. Implement 301 redirects
5. Submit new sitemap to Google
6. Monitor for issues

---

## Deliverables to Client

### Documents (This Repo)
1. ✅ Site Review Analysis
2. ✅ Requirements Document
3. ✅ Design System
4. ✅ Content Model
5. ✅ SEO Strategy
6. ✅ Migration Plan

### Design Phase (Next)
1. Figma mockups for all pages
2. Component library
3. Mobile + Desktop designs

### Development Phase (Next)
1. Fully functional Next.js website
2. Sanity CMS setup and configured
3. All content migrated
4. SEO implementation complete
5. Performance optimized

### Training (Final)
1. 2-hour training session with Tom
2. Written documentation
3. Video tutorials
4. Quick reference guide

---

## Success Metrics

| Metric | Current | 6-Month Target |
|--------|---------|----------------|
| Page Load Time | ~4s | < 2s |
| Lighthouse Score | ~70 | > 90 |
| Organic Traffic | Baseline | +20% |
| Contact Inquiries | Baseline | Maintain or increase |
| Content Update Time | Requires help | < 5 min |

---

## Next Steps

### Immediate Actions
1. **Review with Client** - Present findings and get approval
2. **Confirm Budget** - Discuss timeline and investment
3. **Tech Stack Decision** - Confirm Next.js + Sanity
4. **Kickoff Design** - Begin Figma mockups

### Questions for Tom
1. What's the budget range for this project?
2. Any timeline constraints or deadlines?
3. Does he want to keep the Italian language version?
4. Any specific features from current site he wants changed/removed?
5. Email marketing integration needed?

---

## About This Documentation

**Created:** 2026-05-30  
**Author:** BetterMachine Agency  
**Purpose:** Complete project foundation for replacing Extrusion Supplies Wix website

All documents follow industry best practices for:
- Requirements gathering
- Design systems
- Content modeling
- SEO strategy
- Technical implementation
- Project management

---

## Contact

For questions about this project documentation:
- **Project:** Extrusion Supplies Website Replacement
- **Client:** Tom Nentwick, Extrusion Supplies
- **Current Site:** https://extrusionsupplies.com
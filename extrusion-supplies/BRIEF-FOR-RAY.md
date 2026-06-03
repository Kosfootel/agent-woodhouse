# Extrusion Supplies Website Rebuild — Dev Brief for Ray

**Status:** Ready for Development  
**Assigned:** Ray (Lead Developer)  
**Client:** Tom Nentwick, Extrusion Supplies  
**Prepared by:** Woodhouse — June 2, 2026  

---

## TL;DR

Replace Tom's Wix site with a Next.js + Sanity + Hostinger stack. Tom edits from both Windows Desktop and iPhone. You own the build. All docs are in the repo.

---
- **Client:** Tom Nentwick, Extrusion Supplies
- **Business:** B2B aluminum extrusion equipment broker, Canfield OH
- **Current Site:** Wix (extrusionsupplies.com)
- **Problem:** Slow (~3-4s), poor SEO, limited control, $276/yr
- **Goal:** Modern, fast, SEO-optimized site Tom can manage himself from Windows Desktop AND iPhone

## Tech Stack (Confirmed by Client)
| Component | Selection |
|-----------|-----------|
| Frontend | Next.js 14 |
| CMS | Sanity (headless, cross-platform) |
| Hosting | Hostinger (client preference) |
| Source Control | GitHub (client requirement) |
| Deployment | GitHub Actions → Hostinger |

## Key Requirements
1. **WYSIWYG editing** — Homepage, products, pages — no code
2. **Full mobile parity** — iPhone must have same editing power as Windows Desktop
3. **Camera upload** — Tom can snap product photos on iPhone and publish immediately
4. **SEO** — Structured data, unique meta tags, Core Web Vitals <2.5s
5. **Cost** — ~$48/yr vs current ~$276/yr (83% savings)
6. **Content** — ~100 products, ~50 pages, 20+ categories, English + Italian

## Scope
- 5 core pages: Homepage, Product Listing, Product Detail, Contact, About
- Sanity schemas: Product, Category, Page, Homepage (singleton), Site Settings
- Content migration from Wix + 301 redirects
- Training session for Tom
- Timeline: 6-8 weeks

## Deliverables in Repo
Full documentation exists at: `bettermachine/extrusion-supplies/`
- Requirements, site review, design system, content model
- SEO strategy, migration plan, hosting/deployment guide
- Design and implementation prompts ready

## Ray's Role: Lead Developer

You own this build. Erik and Felix (hockeyops.ai) are a separate track.

**Your responsibilities:**
1. Review all docs in this repo (start with PROJECT-SUMMARY.md)
2. Validate tech stack — flag any Sanity + Hostinger gotchas
3. Build the Next.js frontend
4. Configure Sanity schemas (Product, Category, Page, Homepage, Site Settings)
5. Set up GitHub Actions → Hostinger deployment pipeline
6. Migrate content from Wix (~100 products, ~50 pages)
7. Implement SEO: structured data, meta tags, Core Web Vitals
8. Train Tom (2-hour session)

**Erik is your client.** Woodhouse is documentation + coordination. No other mesh agents involved.

---

## Key Decisions Already Made (Don't Re-litigate)

| Decision | Status |
|----------|--------|
| Next.js 14 | ✅ Confirmed |
| Sanity CMS | ✅ Confirmed |
| Hostinger hosting | ✅ Client preference |
| GitHub source control | ✅ Client requirement |
| iPhone editing parity | ✅ Non-negotiable |
| ~$48/year target cost | ✅ Confirmed |
| Italian i18n | ⚠️ Nice-to-have — confirm with Erik |

---

## Open Questions for You to Resolve

1. **Sanity Studio mobile** — Is the responsive Studio actually usable for daily iPhone product edits? Or do we need a custom mobile UI?
2. **Hostinger Node.js** — Business Shared vs Cloud Startup plan? Static export vs full-stack?
3. **Wix export** — Any tools you recommend for migrating Wix content to Sanity? Manual re-entry?
4. **Image pipeline** — Sanity's asset pipeline + Hostinger CDN, or external (Cloudinary/Imgix)?
5. **i18n approach** — Sanity's approach for Italian, or simpler URL-based fallback?

---

## Deliverables Checklist

- [ ] Review all repo docs
- [ ] Confirm tech stack + hosting plan
- [ ] Set up GitHub repo + Actions
- [ ] Build Next.js frontend (5 core pages)
- [ ] Configure Sanity schemas + Studio
- [ ] Deploy to Hostinger
- [ ] Migrate content from Wix
- [ ] Implement SEO
- [ ] UAT with Erik
- [ ] Launch + handoff to Tom
- [ ] Training session with Tom

---

*Full docs: `~/.openclaw/workspace/bettermachine/extrusion-supplies/`*  
*Questions? Ping Erik or Woodhouse.*
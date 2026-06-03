# Extrusion Supplies - Migration Plan

## 1. Overview

This document outlines the complete process for migrating from Wix to the new custom website, minimizing downtime and preserving SEO value.

**Current Platform:** Wix  
**Target Platform:** [To be determined - Next.js/Sanity recommended]  
**Estimated Timeline:** 6-8 weeks  
**Risk Level:** Medium (URL changes, platform migration)

## 2. Pre-Migration Phase (Week 1)

### 2.1 Discovery & Audit

**Content Inventory:**
```
□ Document all pages (URLs, titles, meta descriptions)
□ Catalog all products (100+ items)
□ List all categories
□ Identify all images and assets
□ Document forms and functionality
□ Note custom features or integrations
```

**Technical Audit:**
```
□ Record current page load times
□ Document current SEO rankings
□ Export Google Analytics data
□ Export Search Console data
□ Test all forms and CTAs
□ Document current redirects (if any)
```

**Content Export from Wix:**

1. **Products:**
   - Wix → CSV export (if available)
   - Manual backup if needed
   - Record all product data fields

2. **Pages:**
   - Copy page content
   - Note all images and their locations
   - Document page hierarchy

3. **Media:**
   - Download all images from Wix CDN
   - Organize by: products, hero, categories, content
   - Note image dimensions and file sizes

### 2.2 URL Mapping

**Current URL Structure (Wix):**
```
Home: /
Product: /product-page/[product-name]
Category: /collections/[category-name]
Pages: /[page-name]
Blog: /blog-posts/[post-name]
```

**New URL Structure:**
```
Home: /
Product: /equipment/[category]/[product-slug]
Category: /equipment/[category]
Pages: /[page-slug]
Blog: /blog/[post-slug]
```

**Redirect Mapping:**
```csv
old_url,new_url,status
https://www.extrusionsupplies.com/product-page/1800-ton-conmetal-press,https://www.extrusionsupplies.com/equipment/extrusion-presses/1800-ton-conmetal-press,301
```

### 2.3 Asset Preparation

**Image Optimization Pipeline:**
1. Download original images from Wix
2. Convert to WebP/AVIF format
3. Generate responsive sizes (400w, 800w, 1200w, 1600w)
4. Optimize file sizes (<200KB per image)
5. Rename with descriptive filenames
6. Organize in folder structure:

```
assets/
├── products/
│   ├── extrusion-presses/
│   ├── ovens/
│   └── ...
├── categories/
├── hero/
├── team/
└── logos/
```

---

## 3. Development Phase (Weeks 2-4)

### 3.1 Environment Setup

```
□ Set up Git repository
□ Set up development environment
□ Set up staging environment
□ Set up production environment
□ Configure CI/CD pipeline
□ Set up CMS (Sanity/Decap)
```

### 3.2 Content Import

**CMS Setup:**
```
□ Define content schemas
□ Set up content types (Product, Category, Page)
□ Configure fields and validations
□ Import products from CSV
□ Import pages
□ Upload and organize images
□ Set up navigation structure
```

**Data Validation:**
```
□ Review all imported products
□ Check image associations
□ Verify category assignments
□ Test all relationships
□ Validate required fields
```

### 3.3 Development Tasks

**Phase 1: Core Site (Week 2)**
```
□ Set up project structure
□ Implement design system
□ Build header component
□ Build footer component
□ Create layout templates
```

**Phase 2: Pages (Week 3)**
```
□ Homepage with CMS integration
□ Product listing page
□ Product detail page
□ Category pages
□ Static pages (About, Contact, etc.)
```

**Phase 3: Features (Week 4)**
```
□ Contact form with validation
□ Search functionality
□ Filtering system
□ Image galleries
□ SEO meta tags
□ Structured data
□ Analytics integration
```

### 3.4 Content Migration Script

```javascript
// Example migration script structure
const migrateProducts = async () => {
  // 1. Read Wix export CSV
  // 2. Transform data to new schema
  // 3. Upload images to CMS
  // 4. Create products in Sanity
  // 5. Log success/errors
};

const migratePages = async () => {
  // Similar process for pages
};

const generateRedirects = () => {
  // Generate redirect config from URL mapping
};
```

---

## 4. Testing Phase (Week 5)

### 4.1 Content Testing

```
□ All products display correctly
□ All images load properly
□ Categories show correct products
□ Navigation works on all pages
□ Search returns correct results
□ Contact form sends emails
□ All links are functional
```

### 4.2 SEO Testing

```
□ All meta titles are present
□ All meta descriptions are present
□ Structured data validates
□ Canonical URLs are correct
□ Sitemap generates properly
□ Robots.txt is correct
□ Open Graph tags work
```

### 4.3 Performance Testing

```
□ Page load times < 2 seconds
□ Lighthouse score > 90
□ Mobile responsiveness verified
□ Image optimization verified
□ Core Web Vitals pass
```

### 4.4 Cross-Browser Testing

```
□ Chrome (latest)
□ Firefox (latest)
□ Safari (latest)
□ Edge (latest)
□ Mobile Safari (iOS)
□ Chrome Mobile (Android)
```

### 4.5 User Acceptance Testing (UAT)

**With Tom:**
```
□ Test CMS workflows:
  - Add a product
  - Edit homepage
  - Update navigation
  - Change images
□ Verify content is correct
□ Confirm editing is intuitive
□ Document any feedback
```

---

## 5. Pre-Launch Phase (Week 6)

### 5.1 SEO Preparation

```
□ Generate XML sitemap
□ Prepare robots.txt
□ Create redirect rules
□ Set up Google Search Console
□ Configure Google Analytics 4
□ Set up Bing Webmaster Tools
□ Verify structured data
```

### 5.2 Analytics Setup

```
□ Google Analytics 4 property
□ Google Tag Manager (optional)
□ Search Console verification
□ Set up conversion tracking
□ Configure goals/events:
  - Contact form submission
  - Phone number clicks
  - Email link clicks
```

### 5.3 Hosting Preparation

```
□ Configure production server
□ Set up SSL certificate
□ Configure CDN
□ Set up backups
□ Configure caching
□ Test domain setup
□ Prepare DNS changes
```

### 5.4 Backup Current Site

```
□ Export complete Wix site
□ Download all images
□ Save all content
□ Document current settings
□ Note any integrations
```

---

## 6. Launch Phase (Week 7)

### 6.1 Launch Day Checklist

**Morning (Pre-Launch):**
```
□ Final content review
□ Final SEO review
□ Performance test
□ All redirects confirmed
□ Backup current site
□ Notify stakeholders
```

**Launch Steps:**
```
□ Step 1: Deploy new site to production
□ Step 2: Update DNS (if changing hosts)
□ Step 3: Configure domain in new host
□ Step 4: Wait for DNS propagation (5-60 min)
□ Step 5: Verify site is live
□ Step 6: Test all critical functions
□ Step 7: Submit sitemap to Google
□ Step 8: Announce completion
```

**Post-Launch (First 4 Hours):**
```
□ Monitor error logs
□ Check contact forms
□ Verify analytics tracking
□ Test on mobile devices
□ Monitor site speed
□ Check for 404 errors
□ Verify redirects work
```

### 6.2 Launch Communication

**To Client:**
```
Subject: Extrusion Supplies Website Migration Complete

The new website is now live at https://www.extrusionsupplies.com

What's new:
- Faster loading
- Better mobile experience
- Easy content management
- Improved SEO

Next steps:
- Review the site
- Test the CMS
- Training session scheduled
```

---

## 7. Post-Launch Phase (Weeks 7-8)

### 7.1 Day 1-2 Monitoring

```
□ Hourly error log checks
□ Contact form testing
□ Mobile functionality
□ Performance monitoring
□ Search Console for crawl errors
□ Analytics for traffic patterns
```

### 7.2 Week 1 Monitoring

```
□ Daily analytics review
□ Search Console review
□ Error log review
□ User feedback collection
□ Fix any critical issues
□ Monitor ranking changes
```

### 7.3 Week 2-4 Monitoring

```
□ Weekly performance reports
□ SEO ranking tracking
□ Search Console issues
□ User feedback review
□ Content updates training
□ Documentation updates
```

### 7.4 Training Session

**With Tom (2 hours):**

1. **CMS Overview (30 min)**
   - Dashboard walkthrough
   - Content types explained
   - Media library

2. **Product Management (45 min)**
   - Add new product
   - Edit existing product
   - Upload images
   - Hide/show products
   - Category assignment

3. **Homepage Management (30 min)**
   - Update hero slides
   - Change featured products
   - Update about section

4. **Page Management (15 min)**
   - Edit static pages
   - Update navigation

**Training Materials:**
- Written guide (PDF)
- Video tutorials (screen recordings)
- Quick reference card
- Support contact info

---

## 8. Risk Mitigation

### 8.1 Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| SEO traffic drop | High | Medium | 301 redirects, sitemap submission, monitoring |
| Data loss | High | Low | Multiple backups, import validation |
| Extended downtime | Medium | Low | Staging testing, quick rollback plan |
| CMS confusion | Medium | Medium | Training, documentation, support |
| Performance issues | Medium | Low | Testing, optimization, CDN |

### 8.2 Rollback Plan

**If Critical Issues Occur:**
1. Document the issue
2. Attempt quick fix (if < 1 hour)
3. If not fixable:
   - Revert DNS to Wix
   - Restore Wix site
   - Notify client
   - Schedule re-launch

**Wix Site Preservation:**
- Keep Wix site active until 30 days post-launch
- Maintain Wix subscription for 1 month
- Don't delete Wix site until confirmed stable

### 8.3 Communication Plan

**Issues Discovered:**
```
□ Immediate notification to client
□ Severity assessment
□ Estimated fix time
□ Workaround options
□ Regular updates until resolved
```

---

## 9. Success Criteria

### 9.1 Technical Success

```
□ 100% of content migrated
□ 0% data loss
□ 100% functional redirects
□ < 2 second page load
□ > 90 Lighthouse score
□ All forms working
□ All images loading
```

### 9.2 Business Success

```
□ Client can update homepage independently
□ Client can add/edit products
□ Traffic maintained or improved
□ Contact form submissions maintained
□ SEO rankings maintained
```

### 9.3 Timeline Success

```
□ Launched within 8 weeks
□ No more than 1 hour downtime
□ Training completed
□ Documentation delivered
```

---

## 10. Appendix

### 10.1 Tools & Resources

**Migration Tools:**
- Wix CSV Export
- Image download scripts
- Redirect generator

**Monitoring Tools:**
- Google Search Console
- Google Analytics 4
- Lighthouse
- Uptime monitoring

**Communication:**
- Project management tool
- Video conferencing
- Screen sharing for training

### 10.2 Contact Information

**Project Team:**
- Project Manager: [Name]
- Developer: [Name]
- Designer: [Name]
- SEO Specialist: [Name]

**Client:**
- Tom Nentwick
- Email: tom@extrusionsupplies.com
- Phone: 330-506-9291

### 10.3 Checklist Summary

**Pre-Migration:**
- [ ] Content inventory complete
- [ ] URL mapping created
- [ ] Assets downloaded and optimized
- [ ] Redirects planned

**Development:**
- [ ] CMS configured
- [ ] Content imported
- [ ] Site developed
- [ ] All features implemented

**Testing:**
- [ ] Content tested
- [ ] SEO validated
- [ ] Performance verified
- [ ] UAT completed

**Launch:**
- [ ] DNS configured
- [ ] Site deployed
- [ ] Redirects active
- [ ] Analytics working

**Post-Launch:**
- [ ] Monitoring active
- [ ] Training completed
- [ ] Documentation delivered
- [ ] Support plan established

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
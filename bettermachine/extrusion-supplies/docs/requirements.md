# Extrusion Supplies - Website Requirements Document

## 1. Executive Summary

### Project Purpose
Replace the existing Wix-based website for Extrusion Supplies with a custom-built solution that maintains ease of use for a novice technology user while improving performance, SEO, and reducing ongoing costs.

### Business Context
- **Business Model:** B2B equipment broker (all transactions offline)
- **Primary Use:** Product catalog browsing and lead generation
- **Content Updates:** Frequent (product availability changes, new equipment)
- **Target Audience:** Industrial aluminum extrusion companies

## 2. Device-Agnostic CMS Requirements

### Critical Requirement: Cross-Platform Editing

**User Story:** As Tom, I want to edit my website from my Windows desktop OR my iPhone with equal ease, so I can make updates whether I'm in the office or on the go.

**Platform Requirements:**
- [ ] Full CMS functionality on **Windows Desktop** (Chrome, Edge, Firefox)
- [ ] Full CMS functionality on **iPhone** (Safari, Chrome iOS)
- [ ] Responsive admin interface that adapts to screen size
- [ ] Touch-optimized controls for mobile editing
- [ ] Image upload works from both desktop files and phone camera/library
- [ ] No desktop-only features (all functions available on mobile)

**Acceptance Criteria:**
- Client can perform ANY edit on iPhone that they can on desktop
- Image upload works from phone camera roll or take photo directly
- Forms are thumb-friendly with large touch targets (44px minimum)
- No horizontal scrolling required on mobile
- Save/publish works reliably on both platforms
- Site preview renders correctly on mobile admin

### 2.1 Homepage Management (Priority: Critical)

**User Story:** As Tom, I want to easily change homepage images and featured products without technical help.

**Requirements:**
- [ ] WYSIWYG image upload/replacement for hero carousel
- [ ] Drag-and-drop reordering of carousel slides
- [ ] Featured products section with checkbox visibility toggle
- [ ] Ability to add/remove featured product cards
- [ ] Text editing for hero headlines and CTAs
- [ ] Preview before publishing changes
- [ ] One-click publish/revert functionality

**Acceptance Criteria:**
- Client can update homepage images in under 2 minutes
- Changes visible on site within 60 seconds of publish
- No HTML/CSS knowledge required
- Mobile preview available

### 2.2 Product Catalog Management (Priority: Critical)

**User Story:** As Tom, I want to add, remove, and hide products from customer view easily.

**Requirements:**
- [ ] "Add Product" form with all necessary fields
- [ ] Product status toggle: Published / Draft / Hidden
- [ ] Bulk actions (hide multiple products, delete, etc.)
- [ ] Product categorization (drag-and-drop into categories)
- [ ] Image upload with automatic optimization
- [ ] Rich text editor for product descriptions
- [ ] Duplicate product functionality
- [ ] Archive (soft delete) vs permanent delete

**Required Product Fields:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Product Name | Text | Yes | Max 100 characters |
| Category | Select | Yes | From predefined list |
| Status | Toggle | Yes | Show/Hide from catalog |
| Price | Text | No | "Contact for pricing" default |
| Condition | Select | Yes | New / Used / Refurbished |
| Manufacturer | Text | Yes | Brand name |
| Model Number | Text | No | Equipment model |
| Year | Number | No | Manufacturing year |
| Description | Rich Text | Yes | Full product details |
| Short Description | Text | Yes | 2-3 sentence summary |
| Main Image | Image | Yes | Hero product image |
| Gallery Images | Images | No | Up to 10 additional images |
| Specifications | Key/Value | No | Technical specs table |
| Location | Text | No | Equipment location |
| Availability | Select | Yes | Available / Sold / Pending |
| SEO Title | Text | No | Auto-generated default |
| SEO Description | Text | No | Auto-generated default |

**Acceptance Criteria:**
- New product can be added in under 5 minutes
- Products can be hidden from view without deleting
- Category changes reflect immediately on site
- Images automatically resized for web

### 2.3 Content Pages (Priority: High)

**User Story:** As Tom, I want to edit static content pages like "About" and "Contact" without coding.

**Pages Required:**
- [ ] Home
- [ ] Browse Equipment (Product Listing)
- [ ] Contact
- [ ] About / Bio
- [ ] Equipment Wanted
- [ ] Facilities
- [ ] Blog/News (optional but recommended)

**Requirements:**
- [ ] Visual page builder for static content
- [ ] Text editing with formatting toolbar
- [ ] Image insertion and alignment
- [ ] Link creation and management
- [ ] Button/link customization
- [ ] Page reordering in navigation

### 2.4 Navigation Management (Priority: High)

**User Story:** As Tom, I want to reorganize my menu and add/remove pages easily.

**Requirements:**
- [ ] Drag-and-drop menu reordering
- [ ] Add/remove menu items
- [ ] Create dropdown/submenus
- [ ] Set custom menu labels (different from page titles)
- [ ] Mobile menu preview
- [ ] Sticky/persistent header option

### 2.5 Brand/Appearance Settings (Priority: Medium)

**User Story:** As Tom, I want to update my logo and brand colors if needed.

**Requirements:**
- [ ] Logo upload and replacement
- [ ] Favicon upload
- [ ] Primary/secondary color picker
- [ ] Font selection (limited, curated options)
- [ ] Footer content editing
- [ ] Social media link management

## 3. Non-Functional Requirements

### 3.1 Performance

**Requirements:**
- [ ] Page load time < 2 seconds on 4G
- [ ] Lighthouse Performance score > 90
- [ ] Image optimization (WebP/AVIF with fallbacks)
- [ ] Lazy loading for images
- [ ] CDN for static assets

### 3.2 SEO (Priority: Critical)

**Requirements:**
- [ ] Customizable meta titles per page
- [ ] Customizable meta descriptions per page
- [ ] Open Graph tags for social sharing
- [ ] Structured data (Schema.org):
  - [ ] Organization markup
  - [ ] LocalBusiness markup
  - [ ] Product markup
  - [ ] BreadcrumbList markup
- [ ] XML sitemap generation
- [ ] Robots.txt management
- [ ] Canonical URLs
- [ ] Alt text for all images
- [ ] Semantic HTML structure
- [ ] Clean URL structure (/category/product-name)
- [ ] HTTPS only

### 3.3 Accessibility

**Requirements:**
- [ ] WCAG 2.1 AA compliance
- [ ] Alt text for all images
- [ ] Keyboard navigation support
- [ ] Screen reader compatibility
- [ ] Color contrast compliance (4.5:1)
- [ ] Focus indicators
- [ ] Skip-to-content links

### 3.4 Security

**Requirements:**
- [ ] HTTPS enforced
- [ ] Content Security Policy
- [ ] Form spam protection (CAPTCHA/honeypot)
- [ ] Secure file uploads (image types only)
- [ ] Regular security updates
- [ ] Backup system

### 3.5 Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile Safari (iOS 14+)
- Chrome Mobile

### 3.6 Analytics & Monitoring

**Requirements:**
- [ ] Google Analytics 4 integration
- [ ] Google Search Console setup
- [ ] Contact form conversion tracking
- [ ] Page view tracking
- [ ] Uptime monitoring

## 4. User Experience Requirements

### 4.1 Mobile Experience

**Requirements:**
- [ ] Responsive design (mobile-first)
- [ ] Touch-friendly tap targets (44px minimum)
- [ ] Mobile-optimized navigation
- [ ] Fast mobile load times
- [ ] Click-to-call phone numbers

### 4.2 Product Catalog UX

**Requirements:**
- [ ] Category filtering
- [ ] Product search
- [ ] Sort options (newest, alphabetical)
- [ ] Product card grid layout
- [ ] Quick view option
- [ ] "Contact about this item" CTA
- [ ] Similar products recommendation

### 4.3 Contact/Lead Generation

**Requirements:**
- [ ] Contact form with validation
- [ ] Form success/error messages
- [ ] Email notifications to Tom
- [ ] Auto-responder to customers
- [ ] Spam filtering

## 5. Technical Requirements

### 5.1 CMS Requirements

**Must Have:**
- Visual/WYSIWYG editing
- Role-based access (Admin, Editor)
- Media library with folders
- Content versioning/history
- Preview before publish
- Scheduled publishing

**Nice to Have:**
- Multi-language support
- Content scheduling
- Workflow approval
- Content duplication

### 5.2 Hosting Requirements

- SSL certificate included
- CDN included
- Daily backups
- Staging environment
- Uptime SLA (99.9%+)
- Support for custom domain

### 5.3 Integrations

**Required:**
- Email service (SendGrid/AWS SES)
- Google Analytics
- Google Search Console

**Optional:**
- Facebook Pixel
- LinkedIn Insights
- Live chat (Tidio, etc.)

## 6. Migration Requirements

### 6.1 Content Migration

- [ ] Export all product data from Wix
- [ ] Export all images with optimization
- [ ] Export page content
- [ ] Preserve existing URLs (redirects)
- [ ] Migrate SEO meta data

### 6.2 URL Redirects

- [ ] 301 redirects for all changed URLs
- [ ] Redirect mapping document
- [ ] Sitemap submission to Google

## 7. Training & Documentation

### 7.1 Admin Training

- [ ] 1-hour training session with Tom
- [ ] Written documentation for common tasks
- [ ] Video tutorials for key workflows
- [ ] Cheat sheet/quick reference guide

### 7.2 Documentation Required

- [ ] How to add/edit a product
- [ ] How to update homepage
- [ ] How to manage images
- [ ] How to edit pages
- [ ] How to update navigation
- [ ] Troubleshooting guide

## 8. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Page Load Time | ~3-4s | <2s | Lighthouse |
| Lighthouse Score | ~70 | >90 | Lighthouse |
| Organic Traffic | Baseline | +20% YoY | Google Analytics |
| Contact Form Submissions | Baseline | Maintain | GA Events |
| Content Update Time | Requires help | <5 min | User testing |

## 9. Constraints & Assumptions

### Constraints
- Budget considerations (recommend discussing)
- Timeline considerations (recommend discussing)
- No e-commerce transactions (catalog only)

### Assumptions
- Client will provide all content and images
- Domain registration will remain with client
- Client has email hosting separate from website

## 10. Appendix

### A. Current Site Stats
- ~50 pages
- ~100 products
- ~8 brand partners
- English + Italian content

### B. Reference Sites
- Industrial equipment sites with good UX
- Modern manufacturing company sites

### C. Glossary
- **WYSIWYG**: What You See Is What You Get - visual editing
- **CMS**: Content Management System
- **SEO**: Search Engine Optimization
- **CDN**: Content Delivery Network

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
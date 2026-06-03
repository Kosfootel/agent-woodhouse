# Extrusion Supplies - SEO Strategy

## 1. Current SEO Assessment

### 1.1 Existing Strengths

✅ **Technical Foundation**
- Proper viewport meta tag for mobile
- Open Graph tags configured
- Sitemap.xml properly structured
- Robots.txt configured
- HTTPS enabled
- Clean URL structure

✅ **Content Structure**
- ~100 product pages
- ~50 content pages
- 100+ indexed pages
- Image alt attributes present

✅ **Brand Signals**
- 20+ years in business
- Established domain authority
- Social media presence (Facebook, LinkedIn)
- Founder visibility (personal brand)

### 1.2 Existing Weaknesses

❌ **Missing Schema Markup**
- No Product schema on product pages
- No Organization/LocalBusiness schema
- No BreadcrumbList schema
- No FAQ schema potential

❌ **On-Page SEO**
- Repetitive meta descriptions across pages
- Generic title tags on product pages
- No canonical tags visible
- Missing H1 optimization

❌ **Content Gaps**
- Limited blog content
- No FAQ sections
- No customer testimonials/reviews
- Limited long-form content

❌ **Technical Issues**
- Wix platform limitations
- Slow page load times (estimated 3-4s)
- No Core Web Vitals optimization
- Limited control over technical SEO

---

## 2. Target Keywords

### 2.1 Primary Keywords (High Intent)

| Keyword | Volume | Difficulty | Priority |
|---------|--------|------------|----------|
| aluminum extrusion equipment | 480/mo | Medium | 1 |
| used extrusion press | 320/mo | Low | 1 |
| extrusion equipment for sale | 260/mo | Low | 1 |
| aluminum extrusion machinery | 210/mo | Medium | 2 |
| extrusion press brokers | 170/mo | Low | 2 |
| used aluminum extrusion equipment | 140/mo | Low | 1 |

### 2.2 Secondary Keywords

| Category | Keywords |
|----------|----------|
| **Equipment Types** | extrusion press, log furnace, aging oven, extrusion puller, cut-off saw, CNC machining center |
| **Brands** | Extral, Thermika, Ichikawa, Emmegi (if dealer/used) |
| **Location** | aluminum extrusion equipment Ohio, extrusion equipment broker USA |
| **Industry** | aluminum extruder equipment, extrusion die equipment |

### 2.3 Long-Tail Keywords

- "1800 ton extrusion press for sale"
- "used aluminum extrusion press line"
- "hydraulic extrusion press equipment"
- "refurbished extrusion machinery"
- "aluminum extrusion equipment broker"

---

## 3. On-Page SEO Strategy

### 3.1 URL Structure

**Current (Wix):**
```
/product-page/[product-name]
```

**Recommended:**
```
/equipment/[category]/[product-slug]

Examples:
/equipment/extrusion-presses/1800-ton-conmetal-press
/equipment/ovens/thermika-log-furnace-2020
/equipment/saws/tru-cut-aluminum-saw
```

**Benefits:**
- Clear hierarchy for users and crawlers
- Keyword-rich URLs
- Scalable structure
- Easy to implement redirects

### 3.2 Title Tag Strategy

**Homepage:**
```
Extrusion Supplies | Used & New Aluminum Extrusion Equipment | Ohio
```

**Category Pages:**
```
[Category Name] for Sale | Used & New [Category] | Extrusion Supplies

Example:
Extrusion Presses for Sale | Used & New Hydraulic Presses | Extrusion Supplies
```

**Product Pages:**
```
[Product Name] | [Condition] | [Manufacturer] | Extrusion Supplies

Examples:
1800 Ton Conmetal Press | Used | Conmetal | Extrusion Supplies
Thermika Log Furnace | New | Thermika | Extrusion Supplies
```

**Content Pages:**
```
[Page Title] | Extrusion Supplies

Example:
About Tom Nentwick | 20+ Years Extrusion Equipment Experience | Extrusion Supplies
```

**Rules:**
- Max 60 characters
- Primary keyword at beginning
- Brand name at end
- Unique for every page

### 3.3 Meta Description Strategy

**Template:**
```
[Product/Category description]. [Condition] [equipment type] available. Contact Tom Nentwick at Extrusion Supplies for pricing and availability. Located in Canfield, OH.
```

**Examples:**

*Product:*
```
Fully refurbished 1800 ton Conmetal extrusion press line. Used hydraulic press in excellent condition. Contact Tom at Extrusion Supplies for pricing and availability. Located in Canfield, OH.
```

*Category:*
```
Browse our selection of used and new extrusion presses for sale. Hydraulic and mechanical presses from top brands. Contact Tom Nentwick at Extrusion Supplies. Located in Canfield, OH.
```

**Rules:**
- Max 155 characters
- Include primary keyword
- Include location
- Include call to action
- Unique per page

### 3.4 Header Tag Structure

**Homepage:**
```html
<h1>Used & New Aluminum Extrusion Equipment</h1>
<h2>Featured Equipment</h2>
<h2>Browse by Category</h2>
<h2>About Extrusion Supplies</h2>
```

**Category Page:**
```html
<h1>[Category Name] for Sale</h1>
<h2>Filter Results</h2>
<h3>[Product Name]</h3> (for each product)
```

**Product Page:**
```html
<h1>[Product Name]</h1>
<h2>Product Details</h2>
<h2>Specifications</h2>
<h2>Related Equipment</h2>
```

**Rules:**
- One H1 per page
- Logical hierarchy (H1 → H2 → H3)
- Include keywords naturally
- Don't skip levels

---

## 4. Structured Data Implementation

### 4.1 Organization Schema (Homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Extrusion Supplies",
  "url": "https://www.extrusionsupplies.com",
  "logo": "https://www.extrusionsupplies.com/logo.png",
  "description": "Serving the aluminum extrusion industry for over 20 years. Quality used and new extrusion equipment.",
  "founder": {
    "@type": "Person",
    "name": "Tom Nentwick"
  },
  "foundingDate": "2004",
  "sameAs": [
    "https://www.facebook.com/extrusionsupplies",
    "https://www.linkedin.com/in/extrusionsupplies"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-330-506-9291",
    "contactType": "sales",
    "availableLanguage": "English"
  }
}
```

### 4.2 LocalBusiness Schema (Homepage + Contact)

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Extrusion Supplies",
  "image": "https://www.extrusionsupplies.com/logo.png",
  "@id": "https://www.extrusionsupplies.com",
  "url": "https://www.extrusionsupplies.com",
  "telephone": "+1-330-506-9291",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[Street Address]",
    "addressLocality": "Canfield",
    "addressRegion": "OH",
    "postalCode": "[ZIP]",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 41.0248,
    "longitude": -80.7601
  },
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday"
    ],
    "opens": "09:00",
    "closes": "17:00"
  },
  "priceRange": "$$$"
}
```

### 4.3 Product Schema (Product Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "1800 Ton Conmetal Extrusion Press",
  "image": [
    "https://www.extrusionsupplies.com/product-1.jpg",
    "https://www.extrusionsupplies.com/product-2.jpg"
  ],
  "description": "Fully refurbished 1800 ton Conmetal extrusion press line...",
  "sku": "1800-conmetal-001",
  "brand": {
    "@type": "Brand",
    "name": "Conmetal"
  },
  "manufacturer": {
    "@type": "Organization",
    "name": "Conmetal"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://www.extrusionsupplies.com/equipment/extrusion-presses/1800-ton-conmetal-press",
    "itemCondition": "https://schema.org/UsedCondition",
    "availability": "https://schema.org/InStock",
    "price": "0",
    "priceCurrency": "USD",
    "priceValidUntil": "2026-12-31",
    "seller": {
      "@type": "LocalBusiness",
      "name": "Extrusion Supplies"
    }
  }
}
```

### 4.4 Breadcrumb Schema (All Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://www.extrusionsupplies.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Extrusion Presses",
      "item": "https://www.extrusionsupplies.com/equipment/extrusion-presses"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "1800 Ton Conmetal Press"
    }
  ]
}
```

### 4.5 WebSite Schema (Homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "url": "https://www.extrusionsupplies.com",
  "name": "Extrusion Supplies",
  "description": "Used and new aluminum extrusion equipment",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://www.extrusionsupplies.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

---

## 5. Content Strategy

### 5.1 Blog Content Plan

**Target:** 2-4 posts per month

**Topic Ideas:**

1. **Equipment Guides** (Educational)
   - "How to Choose the Right Extrusion Press for Your Operation"
   - "Used vs. New Extrusion Equipment: A Buyer's Guide"
   - "Understanding Tonnage: What Size Press Do You Need?"

2. **Industry News** (Timely)
   - "2024 Aluminum Extrusion Industry Trends"
   - "New Equipment Arrivals at Extrusion Supplies"

3. **Case Studies** (Social Proof)
   - "How [Company] Expanded with Refurbished Equipment"
   - "From Startup to Scale: Equipment Solutions"

4. **FAQ Content** (Long-tail SEO)
   - "What is an Aluminum Extrusion Press?"
   - "How Much Does Extrusion Equipment Cost?"
   - "What to Look for When Buying Used Extrusion Equipment"

### 5.2 Page Content Recommendations

**About Page:**
- Expand Tom's bio (500+ words)
- Include founder photo
- Add company history/timeline
- Include mission/values

**Category Pages:**
- 200-300 words of unique content
- Include category overview
- Mention popular brands in category
- Link to related categories

**Product Pages:**
- Detailed descriptions (150+ words)
- Specifications table
- Multiple images with zoom
- Related equipment section

### 5.3 FAQ Page

Create a comprehensive FAQ page targeting common questions:

- How does the buying process work?
- Do you ship equipment internationally?
- What condition are used machines in?
- Can I inspect equipment before purchase?
- Do you offer financing?
- What warranty comes with equipment?
- How do I sell my used equipment?

---

## 6. Technical SEO Requirements

### 6.1 Core Web Vitals Targets

| Metric | Target | Current (Wix) |
|--------|--------|---------------|
| LCP (Largest Contentful Paint) | < 2.5s | ~4s |
| FID (First Input Delay) | < 100ms | ~200ms |
| CLS (Cumulative Layout Shift) | < 0.1 | ~0.15 |

### 6.2 Performance Optimizations

- Image optimization (WebP/AVIF with fallbacks)
- Lazy loading for images below fold
- Critical CSS inlining
- JavaScript code splitting
- CDN for static assets
- Browser caching headers

### 6.3 Mobile Optimization

- Responsive design
- Touch-friendly tap targets (44px minimum)
- Mobile-first indexing compliance
- AMP (optional, not critical for B2B)

### 6.4 Indexing & Crawling

**Sitemap Structure:**
```xml
/sitemap.xml (index)
├── /sitemap-pages.xml
├── /sitemap-products.xml
├── /sitemap-categories.xml
└── /sitemap-blog.xml
```

**Robots.txt:**
```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /checkout/  (if applicable)
Sitemap: https://www.extrusionsupplies.com/sitemap.xml
```

---

## 7. Local SEO

### 7.1 Google Business Profile

**Action Items:**
- [ ] Claim/verify Google Business Profile
- [ ] Complete all business information
- [ ] Add high-quality photos
- [ ] Encourage customer reviews
- [ ] Post regular updates
- [ ] Add products/services

**Business Categories:**
- Primary: Industrial Equipment Supplier
- Secondary: Machinery Dealer, Used Machinery Dealer

### 7.2 Local Citations

Ensure consistent NAP (Name, Address, Phone) across:

- Google Business Profile
- Yelp for Business
- LinkedIn Company Page
- Facebook Business Page
- Industry directories
- ThomasNet (if applicable)

### 7.3 Location Pages

Create location-specific content:

- Service area: Ohio, Midwest, USA
- "Equipment for sale in [State]" pages (if expanding)
- Local keywords in content

---

## 8. Link Building Strategy

### 8.1 Internal Linking

**Strategy:**
- Link from homepage to category pages
- Link from categories to products
- Cross-link related products
- Breadcrumb navigation
- Related equipment sections

**Anchor Text:**
- Use descriptive keywords
- Avoid "click here"
- Vary anchor text naturally

### 8.2 External Link Building

**Industry Directories:**
- ThomasNet.com
- IndustryNet.com
- Kompass.com
- MacRAE's Blue Book

**Industry Associations:**
- Aluminum Extruders Council (AEC)
- Local manufacturing associations

**Content Marketing:**
- Guest posts on industry blogs
- Equipment guides as linkable assets
- Original research/reports

**Partnerships:**
- Equipment manufacturers (backlinks)
- Service providers
- Industry publications

---

## 9. Measurement & Reporting

### 9.1 KPIs

| Metric | Baseline | 6-Month Target | 12-Month Target |
|--------|----------|----------------|-----------------|
| Organic Sessions | Current | +20% | +40% |
| Keyword Rankings (Top 10) | Current | +10 | +20 |
| Contact Form Submissions | Current | +15% | +30% |
| Page Load Time | ~4s | <2.5s | <2s |
| Core Web Vitals | Fails | Passes | Passes |
| Indexed Pages | Current | +50 | +100 |

### 9.2 Tools Setup

**Required:**
- Google Analytics 4
- Google Search Console
- Google Business Profile
- Bing Webmaster Tools (optional)

**Tracking Setup:**
- Event tracking for contact forms
- E-commerce tracking (if applicable)
- Scroll depth tracking
- Outbound link tracking

### 9.3 Reporting Schedule

- **Weekly:** Traffic overview, new keywords
- **Monthly:** Full SEO report, ranking changes
- **Quarterly:** Strategy review, competitor analysis

---

## 10. Migration SEO Checklist

### Pre-Migration

- [ ] Document all current URLs
- [ ] Export all meta titles/descriptions
- [ ] Record current rankings
- [ ] Set up Google Analytics 4
- [ ] Set up Google Search Console

### Migration

- [ ] Implement 301 redirects (all old URLs → new)
- [ ] Transfer meta titles/descriptions
- [ ] Implement structured data
- [ ] Submit new sitemap
- [ ] Update internal links

### Post-Migration

- [ ] Monitor 404 errors
- [ ] Check index status in GSC
- [ ] Verify structured data validation
- [ ] Monitor ranking changes
- [ ] Update Google Business Profile URL

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
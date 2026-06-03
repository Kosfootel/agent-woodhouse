# Implementation Prompt: Extrusion Supplies Website

## Project Overview

Build a modern, fast, SEO-optimized website to replace the current Wix site for Extrusion Supplies. The site must be easy for a novice user (Tom) to manage via a headless CMS.

**Current Site:** https://extrusionsupplies.com  
**Tech Stack:** Next.js 14 (App Router) + Sanity CMS + **Hostinger** + **GitHub**  
**Timeline:** 6-8 weeks

**Client-Specified Infrastructure:**
- ✅ **Hosting:** Hostinger (client preference)
- ✅ **Source Control:** GitHub (client requirement)
- ✅ **CMS:** Sanity (cross-platform editing)
- ✅ **Frontend:** Next.js (SEO + performance)

## Technical Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui + custom components
- **Icons:** Lucide React
- **Animations:** Framer Motion (minimal, purposeful)

### CMS
- **Platform:** Sanity CMS
- **Schema:** Custom schemas for products, pages, categories
- **Images:** Sanity Image CDN with optimization
- **Cross-Platform:** Full editing on Windows Desktop AND iPhone

### Hosting & Infrastructure (Client-Specified)
- **Platform:** Hostinger (Business Shared or Cloud)
- **Source Control:** GitHub (repository + GitHub Actions)
- **Deployment:** GitHub Actions → Hostinger
- **CDN:** Hostinger CDN (included)
- **SSL:** Free SSL certificate (Hostinger)
- **Analytics:** Google Analytics 4

### SEO & Performance
- **Meta:** next/head for SEO
- **Images:** next/image with optimization
- **Sitemap:** Static sitemap generation
- **Structured Data:** jsonld

## Project Structure

```
extrusion-supplies/
├── .github/
│   └── workflows/
│       ├── deploy.yml         # GitHub Actions: Build & deploy to Hostinger
│       └── test.yml           # Run tests on PRs
├── src/                        # Next.js application
│   ├── app/                    # App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── equipment/
│   │   ├── product/
│   │   ├── about/
│   │   ├── contact/
│   │   └── api/
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   ├── sections/
│   │   └── product/
│   ├── lib/
│   │   └── sanity/
│   └── types/
├── sanity/                     # Sanity Studio
│   ├── schemas/
│   ├── config/
│   └── sanity.config.ts
├── public/                     # Static assets
├── .env.example               # Environment variables
├── .env.local                 # Local secrets (gitignored)
├── next.config.js             # Next.js config (static export for Hostinger)
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Implementation Phases

### Phase 1: Setup & Foundation (Week 1)

**Tasks:**
```bash
# 1. Initialize project
npx create-next-app@latest my-app --typescript --tailwind --app

# 2. Install dependencies
cd my-app
npm install @sanity/client @sanity/image-url groq
npm install framer-motion lucide-react
npm install @radix-ui/react-dialog @radix-ui/react-slot
npm install class-variance-authority clsx tailwind-merge

# 3. Setup shadcn components
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card badge dialog input select

# 4. Setup Sanity
npm install -g @sanity/cli
sanity init
```

**Deliverables:**
- [ ] Project repository set up
- [ ] Development environment running
- [ ] Sanity project created
- [ ] Basic folder structure
- [ ] TypeScript types defined
- [ ] Tailwind config with design tokens

### Phase 2: CMS Schemas (Week 1-2)

**Sanity Schemas to Create:**

1. **Product Schema** (`sanity/schemas/product.ts`)
```typescript
export default {
  name: 'product',
  type: 'document',
  title: 'Product',
  fields: [
    { name: 'name', type: 'string', title: 'Product Name', validation: Rule => Rule.required() },
    { name: 'slug', type: 'slug', title: 'Slug', options: { source: 'name' } },
    { name: 'category', type: 'reference', to: [{ type: 'category' }] },
    { name: 'condition', type: 'string', options: { list: ['new', 'used', 'refurbished'] } },
    { name: 'manufacturer', type: 'string' },
    { name: 'modelNumber', type: 'string' },
    { name: 'year', type: 'number' },
    { name: 'shortDescription', type: 'text', rows: 3 },
    { name: 'description', type: 'array', of: [{ type: 'block' }] },
    { name: 'mainImage', type: 'image', options: { hotspot: true } },
    { name: 'gallery', type: 'array', of: [{ type: 'image' }] },
    { name: 'availability', type: 'string', options: { list: ['available', 'sold', 'pending', 'coming-soon'] } },
    { name: 'featured', type: 'boolean', initialValue: false },
    { name: 'seoTitle', type: 'string' },
    { name: 'seoDescription', type: 'text' },
  ]
}
```

2. **Category Schema** (`sanity/schemas/category.ts`)
3. **Page Schema** (`sanity/schemas/page.ts`)
4. **Site Settings Schema** (`sanity/schemas/siteSettings.ts`)
5. **Homepage Schema** (`sanity/schemas/homepage.ts`)

**Deliverables:**
- [ ] All Sanity schemas created
- [ ] Test content added in Sanity Studio
- [ ] GROQ queries written
- [ ] TypeScript types generated

### Phase 3: Core Components (Week 2)

**Layout Components:**

1. **Header Component**
```typescript
// components/layout/Header.tsx
interface HeaderProps {
  siteSettings: SiteSettings;
}

export function Header({ siteSettings }: HeaderProps) {
  // Sticky header with logo, nav, mobile menu
  // Use shadcn Sheet for mobile menu
}
```

2. **Footer Component**
3. **Container Component** (max-width wrapper)

**Section Components:**

1. **HeroCarousel**
   - Auto-advance every 5 seconds
   - Pause on hover
   - Touch/swipe support
   - Dots + arrow navigation
   - Image optimization with next/image

2. **CategoryGrid**
   - Responsive grid (3x2, 2x3, scrollable)
   - Hover effects
   - Link to category pages

3. **FeaturedProducts**
   - Horizontal scroll on mobile
   - Product cards with badges

4. **AboutSection**
   - Two-column responsive layout
   - Image + text

5. **PartnerLogos**
   - Grayscale → color on hover
   - Responsive horizontal layout

6. **ContactCTA**
   - Full-width dark section
   - Prominent CTAs

**Deliverables:**
- [ ] All layout components
- [ ] All section components
- [ ] Responsive styling
- [ ] Accessible markup

### Phase 4: Pages (Week 3)

**Homepage** (`app/page.tsx`)
```typescript
export default async function HomePage() {
  const homepage = await getHomepage();
  const featuredProducts = await getFeaturedProducts();
  
  return (
    <>
      <HeroCarousel slides={homepage.heroSlides} />
      <CategoryGrid categories={homepage.featuredCategories} />
      <FeaturedProducts products={featuredProducts} />
      <AboutSection content={homepage.aboutSection} />
      <PartnerLogos partners={homepage.partners} />
      <ContactCTA />
    </>
  );
}
```

**Product Listing** (`app/equipment/page.tsx`)
- Fetch all products
- Implement filters (category, condition, availability)
- Grid/list view toggle
- Pagination
- Search functionality

**Product Detail** (`app/product/[slug]/page.tsx`)
- Generate static params
- Image gallery
- Product info
- Related products
- Contact CTA

**Static Pages** (`app/about/page.tsx`, `app/contact/page.tsx`)
- About page with rich content
- Contact page with form

**Deliverables:**
- [ ] All 5+ pages implemented
- [ ] Dynamic routes working
- [ ] Static generation for products
- [ ] Contact form with validation

### Phase 5: SEO & Performance (Week 4)

**SEO Implementation:**

1. **Metadata** (`app/layout.tsx`)
```typescript
export const metadata: Metadata = {
  title: {
    template: '%s | Extrusion Supplies',
    default: 'Extrusion Supplies | Used & New Aluminum Extrusion Equipment',
  },
  description: '...',
  openGraph: {
    type: 'website',
    locale: 'en_US',
  },
};
```

2. **Page-specific metadata**
```typescript
// app/product/[slug]/page.tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const product = await getProduct(params.slug);
  return {
    title: product.seoTitle || `${product.name} | Extrusion Supplies`,
    description: product.seoDescription,
    openGraph: {
      images: [urlFor(product.mainImage).url()],
    },
  };
}
```

3. **Structured Data**
```typescript
// Add JSON-LD to pages
const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: product.name,
  // ...
};
```

4. **Sitemap** (`app/sitemap.ts`)
```typescript
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const products = await getAllProducts();
  const categories = await getAllCategories();
  
  return [
    { url: 'https://extrusionsupplies.com', lastModified: new Date() },
    ...products.map(p => ({ url: `https://extrusionsupplies.com/product/${p.slug}`, lastModified: p._updatedAt })),
    ...categories.map(c => ({ url: `https://extrusionsupplies.com/equipment/${c.slug}`, lastModified: c._updatedAt })),
  ];
}
```

**Performance Optimization:**
- [ ] Image optimization with next/image
- [ ] Lazy loading for below-fold images
- [ ] Font optimization
- [ ] Bundle analysis and optimization
- [ ] Core Web Vitals optimization

**Deliverables:**
- [ ] Meta tags on all pages
- [ ] Structured data implemented
- [ ] Sitemap generated
- [ ] Robots.txt configured
- [ ] Lighthouse score > 90

### Phase 6: CMS Integration & Admin (Week 5)

**Sanity Studio Customization:**

1. **Desk Structure** - Organize content types
2. **Previews** - Live preview of pages
3. **Dashboard** - Custom dashboard for Tom
4. **Workflows** - Simple publish workflow

**Key Features for Tom (Cross-Platform):**
- Easy product creation form (works on desktop AND iPhone)
- Image upload with preview (camera roll + take photo on mobile)
- Rich text editor for descriptions (mobile-optimized toolbar)
- Status toggle (published/hidden) - large touch-friendly
- Featured product checkbox
- Homepage section editing (responsive layout)
- **Mobile-specific:** Bottom sheet navigation, swipe gestures, camera integration
- **Desktop-specific:** Drag-and-drop, keyboard shortcuts, larger previews

**Sanity Mobile Optimization:**
- Custom theme with larger touch targets (44px minimum)
- Responsive preview panel
- Mobile-friendly image upload (direct from camera)
- Simplified mobile navigation
- Thumb-friendly button sizes

**Deliverables:**
- [ ] Sanity Studio deployed
- [ ] Custom desk structure
- [ ] Preview functionality
- [ ] Documentation for Tom

### Phase 7: Testing & QA (Week 5-6)

**Testing Checklist:**

**CMS Testing (Cross-Platform):**
- [ ] Full CMS functionality on Windows Desktop (Chrome, Edge)
- [ ] Full CMS functionality on iPhone (Safari, Chrome)
- [ ] Image upload from desktop files
- [ ] Image upload from iPhone camera/camera roll
- [ ] Touch-friendly controls (44px minimum targets)
- [ ] No horizontal scrolling on mobile
- [ ] Forms usable with thumbs (no tiny inputs)
- [ ] Preview works on both platforms
- [ ] Save/publish reliable on both platforms

**Functionality:**
- [ ] All links work
- [ ] Contact form submits
- [ ] Search works
- [ ] Filters work
- [ ] Mobile menu works
- [ ] Image galleries work
- [ ] Carousel works

**SEO:**
- [ ] Meta titles present
- [ ] Meta descriptions present
- [ ] Canonical URLs correct
- [ ] Structured data validates
- [ ] Sitemap accessible
- [ ] Robots.txt correct

**Performance:**
- [ ] Page load < 2 seconds
- [ ] Images optimized
- [ ] No console errors
- [ ] Lighthouse > 90

**Accessibility:**
- [ ] ARIA labels
- [ ] Keyboard navigation
- [ ] Color contrast
- [ ] Screen reader tested

**Cross-browser:**
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Safari
- [ ] Chrome Mobile

**Deliverables:**
- [ ] Test report
- [ ] Bug fixes complete
- [ ] UAT signoff

### Phase 8: Launch (Week 7)

**Pre-launch:**
- [ ] Final content review
- [ ] DNS configured
- [ ] SSL certificate
- [ ] Redirects configured
- [ ] Analytics verified

**Launch:**
- [ ] Deploy to production
- [ ] Update DNS
- [ ] Test live site
- [ ] Submit sitemap

**Post-launch:**
- [ ] Monitor for errors
- [ ] Performance monitoring
- [ ] Search Console monitoring

## Key Implementation Details

### Image Handling

```typescript
// lib/sanity/image.ts
import imageUrlBuilder from '@sanity/image-url';

const builder = imageUrlBuilder(client);

export function urlFor(source: any) {
  return builder.image(source);
}

// Usage in component
<Image
  src={urlFor(product.mainImage).width(800).height(600).url()}
  alt={product.name}
  width={800}
  height={600}
/>
```

### Querying Data

```typescript
// lib/sanity/queries.ts
export const productsQuery = groq`
  *[_type == "product" && status == "published"] {
    _id,
    name,
    slug,
    category->,
    mainImage,
    condition,
    availability,
    shortDescription
  }
`;

export const productBySlugQuery = groq`
  *[_type == "product" && slug.current == $slug][0] {
    ...,
    category->,
    gallery[] {
      ...,
      asset->
    }
  }
`;
```

### Form Handling

```typescript
// app/api/contact/route.ts
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const data = await request.json();
  
  // Validate data
  // Send email
  // Store in Sanity (optional)
  
  return NextResponse.json({ success: true });
}
```

## Performance Targets

| Metric | Target |
|--------|--------|
| LCP | < 2.5s |
| FID | < 100ms |
| CLS | < 0.1 |
| Lighthouse | > 90 |
| Page Load | < 2s |
| Time to Interactive | < 3.5s |

## Error Handling

**404 Pages:**
- Custom 404 page with search
- Suggested products
- Navigation help

**Error Boundaries:**
- Global error boundary
- Component-level error handling
- Fallback UI for broken content

**Loading States:**
- Skeleton screens for products
- Loading spinners for forms
- Progressive image loading

## Security Considerations

- Input validation on all forms
- Rate limiting on API routes
- Content Security Policy headers
- Secure image uploads
- No sensitive data in client-side code
- Environment variables secured in GitHub Secrets

---

## Hostinger + GitHub Deployment Guide

### Phase: Infrastructure Setup (Week 1)

**1. GitHub Repository Setup**

```bash
# Create new GitHub repository
# Repository name: extrusion-supplies
# Private or Public (client preference)

# Clone locally
git clone https://github.com/[username]/extrusion-supplies.git
cd extrusion-supplies
```

**2. Hostinger Account Setup**

```
□ Sign up for Hostinger Business Shared or Cloud plan
□ Enable SSH access
□ Note FTP/SFTP credentials
□ Set up primary domain: extrusionsupplies.com
□ Enable free SSL certificate
□ Enable CDN
```

**3. GitHub Actions Configuration**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Hostinger

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run tests
      run: npm test
      
    - name: Build Next.js app
      run: npm run build
      env:
        NEXT_PUBLIC_SANITY_PROJECT_ID: ${{ secrets.SANITY_PROJECT_ID }}
        NEXT_PUBLIC_SANITY_DATASET: ${{ secrets.SANITY_DATASET }}
        SANITY_API_TOKEN: ${{ secrets.SANITY_API_TOKEN }}
        
    - name: Export static site
      run: npm run export
      
    - name: Deploy to Hostinger
      uses: SamKirkland/FTP-Deploy-Action@4.3.3
      with:
        server: ${{ secrets.HOSTINGER_FTP_SERVER }}
        username: ${{ secrets.HOSTINGER_FTP_USERNAME }}
        password: ${{ secrets.HOSTINGER_FTP_PASSWORD }}
        local-dir: ./out/
        server-dir: /public_html/
```

**4. Environment Variables (GitHub Secrets)**

Add to GitHub Repository Settings → Secrets:

```
SANITY_PROJECT_ID=xxx
SANITY_DATASET=production
SANITY_API_TOKEN=xxx
HOSTINGER_FTP_SERVER=ftp.extrusionsupplies.com
HOSTINGER_FTP_USERNAME=xxx
HOSTINGER_FTP_PASSWORD=xxx
```

**5. Next.js Configuration for Hostinger**

Update `next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true, // Required for static export
  },
  trailingSlash: true,
}

module.exports = nextConfig
```

### Deployment Workflow

**Developer Workflow:**
```
1. Make changes locally
2. Test with: npm run dev
3. Commit: git add . && git commit -m "message"
4. Push: git push origin main
5. GitHub Actions automatically:
   - Runs tests
   - Builds Next.js app
   - Exports static HTML
   - Deploys to Hostinger via FTP
6. Site updates automatically
```

**Client Benefits:**
- ✅ No manual FTP uploads
- ✅ Version control (can rollback)
- ✅ Automated testing before deploy
- ✅ Easy collaboration
- ✅ Deployment history

### Alternative: Full-Stack on Hostinger VPS

If API routes are needed (contact form, search):

**Option A:** Static Export + Formspree (for forms)
- Contact forms use Formspree or similar
- Search uses client-side filtering
- **Simplest option**

**Option B:** Hostinger VPS (Premium plan)
- Full Node.js hosting
- API routes work normally
- More complex setup
- **Full-featured option**

**Recommended:** Start with Option A (static export), upgrade if needed.

---

**Output:** Fully functional Next.js application with Sanity CMS, deployed to Hostinger via GitHub Actions, with all documentation.
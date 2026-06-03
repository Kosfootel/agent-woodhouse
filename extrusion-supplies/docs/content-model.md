# Extrusion Supplies - Content Model

## 1. Overview

This document defines the content structure and data schema for the Extrusion Supplies CMS. The model supports easy content management for a novice user while providing flexibility for future growth.

## 2. Content Types

### 2.1 Product

**Purpose:** Individual equipment listings  
**Single Instance:** No (100+ products expected)  
**URL Pattern:** `/equipment/[product-slug]`

#### Schema

```typescript
interface Product {
  _id: string;                    // Auto-generated
  _type: 'product';
  
  // Basic Info
  name: string;                    // Required, max 100 chars
  slug: string;                    // Auto-generated from name
  status: 'draft' | 'published' | 'hidden';
  
  // Categorization
  category: Reference;             // -> Category
  subcategories: Reference[];      // Optional subcategories
  
  // Equipment Details
  condition: 'new' | 'used' | 'refurbished';
  manufacturer: string;            // Brand name
  modelNumber: string;             // Optional
  year: number;                    // Manufacturing year, optional
  serialNumber: string;            // Optional, internal use
  
  // Pricing
  priceType: 'fixed' | 'contact' | 'auction';
  price: number;                   // If fixed
  priceCurrency: string;           // Default: USD
  
  // Content
  shortDescription: string;        // Required, max 300 chars
  description: PortableText;       // Rich text, required
  specifications: KeyValue[];      // Technical specs table
  
  // Location
  location: string;                // Where equipment is located
  availability: 'available' | 'sold' | 'pending' | 'coming-soon';
  
  // Media
  mainImage: Image;                // Required
  gallery: Image[];                // Up to 10 images
  videos: Video[];                 // Optional
  documents: File[];               // PDFs, manuals, etc.
  
  // SEO
  seoTitle: string;                // Auto: "{name} | Extrusion Supplies"
  seoDescription: string;          // Auto from shortDescription
  keywords: string[];              // Optional
  
  // Metadata
  createdAt: DateTime;
  updatedAt: DateTime;
  publishedAt: DateTime;
  
  // Display
  featured: boolean;               // Show on homepage
  featuredOrder: number;           // Sort order for featured
}

interface KeyValue {
  key: string;
  value: string;
}
```

#### Field Descriptions

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Product display name | "1800 Ton Conmetal Extrusion Press" |
| `slug` | URL-friendly identifier | "1800-ton-conmetal-press" |
| `status` | Visibility in admin vs site | published |
| `condition` | Equipment condition | used |
| `priceType` | How price is displayed | contact |
| `shortDescription` | Card display text | "Fully refurbished 1800 ton press line ready for immediate delivery..." |
| `availability` | Current status | available |
| `featured` | Homepage carousel | true |

#### Product Status Workflow

```
Draft → Published → Hidden
   ↑       ↓         ↓
   └───────┴─────────┘ (can revert)
```

- **Draft:** Not visible on site, working copy
- **Published:** Visible on site
- **Hidden:** Removed from site but preserved in CMS

---

### 2.2 Category

**Purpose:** Product categorization for browsing  
**Single Instance:** No  
**URL Pattern:** `/browse/[category-slug]`

#### Schema

```typescript
interface Category {
  _id: string;
  _type: 'category';
  
  // Basic Info
  name: string;                    // Required
  slug: string;                    // Auto-generated
  description: string;             // Optional, for SEO
  
  // Hierarchy
  parent: Reference;               // -> Category (for subcategories)
  order: number;                   // Sort position
  
  // Display
  image: Image;                    // Category thumbnail
  icon: string;                    // Optional icon name
  
  // Content
  content: PortableText;           // Category page content
  featuredProducts: Reference[];   // Featured products in category
  
  // SEO
  seoTitle: string;
  seoDescription: string;
  
  // Settings
  showInNavigation: boolean;       // Include in main nav
  showInFooter: boolean;           // Include in footer links
}
```

#### Category Hierarchy

```
Browse Equipment (root)
├── Extrusion Presses
│   ├── Hydraulic Presses
│   └── Mechanical Presses
├── Ovens & Furnaces
│   ├── Log Furnaces
│   └── Aging Ovens
├── Pullers
├── Saws
├── CNC Machines
├── Die Equipment
├── Packaging Materials
├── Safety Products
├── Hydraulic Components
├── Billet Equipment
├── Finishing Lines
├── Fabrication Equipment
└── Miscellaneous
```

---

### 2.3 Homepage

**Purpose:** Landing page configuration  
**Single Instance:** Yes (Singleton)  
**URL:** `/`

#### Schema

```typescript
interface Homepage {
  _id: 'homepage';
  _type: 'homepage';
  
  // Hero Section
  heroSlides: HeroSlide[];         // Carousel slides
  
  // Featured Section
  featuredTitle: string;            // Default: "Featured Equipment"
  featuredProducts: Reference[];    // -> Product[], max 6
  featuredLink: Reference;            // Link to "View All"
  
  // Categories Section
  showCategories: boolean;
  categoriesTitle: string;          // Default: "Browse by Category"
  featuredCategories: Reference[];  // -> Category[], max 6
  
  // About Section
  showAbout: boolean;
  aboutContent: PortableText;
  aboutImage: Image;
  
  // Partners/Brands
  showPartners: boolean;
  partnersTitle: string;
  partners: Partner[];
  
  // Contact CTA
  ctaTitle: string;                 // Default: "Looking for Equipment?"
  ctaText: string;
  ctaButtonText: string;
  ctaButtonLink: string;
  
  // SEO
  seoTitle: string;                 // Default: "Extrusion Supplies | ..."
  seoDescription: string;
}

interface HeroSlide {
  _key: string;
  image: Image;
  headline: string;
  subheadline: string;
  ctaText: string;
  ctaLink: string;
  overlayOpacity: number;          // 0-100
  textAlignment: 'left' | 'center' | 'right';
}

interface Partner {
  _key: string;
  name: string;
  logo: Image;
  website: URL;
}
```

#### Homepage Sections (Order)

1. **Hero Carousel** - Full-width, configurable slides
2. **Featured Products** - Grid of highlighted equipment
3. **Category Grid** - Browse by category
4. **About Section** - Company/founder info
5. **Partner Logos** - Brand partners
6. **Contact CTA** - Call to action

---

### 2.4 Page

**Purpose:** Static content pages  
**Single Instance:** No  
**URL Pattern:** `/[page-slug]`

#### Schema

```typescript
interface Page {
  _id: string;
  _type: 'page';
  
  // Basic Info
  title: string;                   // Required
  slug: string;                    // Auto-generated
  
  // Content
  content: PortableText;           // Rich text content
  sections: Section[];             // Modular sections (optional)
  
  // Settings
  showInNavigation: boolean;
  navigationLabel: string;         // Menu text (if different from title)
  parent: Reference;               // For nested pages
  order: number;                   // Menu sort order
  
  // SEO
  seoTitle: string;
  seoDescription: string;
  ogImage: Image;                  // Social share image
  
  // Sidebar
  showSidebar: boolean;
  sidebarContent: PortableText;
}
```

#### Default Pages

| Page | Purpose | URL |
|------|---------|-----|
| About | Company/founder bio | `/about` |
| Contact | Contact info + form | `/contact` |
| Equipment Wanted | Buy requests | `/equipment-wanted` |
| Facilities | Warehouse/facility info | `/facilities` |
| Privacy Policy | Legal | `/privacy` |
| Terms of Service | Legal | `/terms` |

---

### 2.5 Site Settings

**Purpose:** Global site configuration  
**Single Instance:** Yes (Singleton)

#### Schema

```typescript
interface SiteSettings {
  _id: 'siteSettings';
  _type: 'siteSettings';
  
  // Company Info
  companyName: string;             // "Extrusion Supplies"
  tagline: string;                 // "Serving the Aluminum..."
  description: string;             // Short company description
  
  // Contact
  phone: string;                   // 330-506-9291
  email: string;                   // tom@extrusionsupplies.com
  address: {
    street: string;
    city: string;
    state: string;                 // OH
    zip: string;
    country: string;               // USA
  };
  
  // Social Media
  socialLinks: {
    facebook?: URL;
    linkedin?: URL;
    twitter?: URL;
    youtube?: URL;
  };
  
  // Branding
  logo: Image;
  logoWhite: Image;                // For dark backgrounds
  favicon: Image;
  
  // Header
  navigation: NavigationItem[];
  
  // Footer
  footerText: PortableText;
  footerLinks: NavigationItem[];
  
  // SEO Defaults
  defaultSeoTitle: string;
  defaultSeoDescription: string;
  defaultOgImage: Image;
  
  // Analytics
  googleAnalyticsId: string;
  googleTagManagerId: string;
  facebookPixelId: string;
  
  // Technical
  contactFormEmail: string;        // Where contact forms go
  maintenanceMode: boolean;
}

interface NavigationItem {
  _key: string;
  label: string;
  type: 'page' | 'url' | 'category';
  page: Reference;                 // If type = page
  category: Reference;             // If type = category
  url: URL;                        // If type = url
  openInNewTab: boolean;
  children: NavigationItem[];      // For dropdowns
}
```

---

### 2.6 Contact Submission

**Purpose:** Store contact form submissions  
**Single Instance:** No  
**System Type:** Auto-created

#### Schema

```typescript
interface ContactSubmission {
  _id: string;
  _type: 'contactSubmission';
  
  name: string;
  email: string;
  phone: string;
  company: string;
  subject: string;
  message: string;
  
  // Product interest (optional)
  productInterest: Reference;      // -> Product
  
  // Metadata
  submittedAt: DateTime;
  ipAddress: string;
  userAgent: string;
  
  // Status
  status: 'new' | 'replied' | 'archived' | 'spam';
  notes: string;                   // Internal notes
}
```

---

## 3. Reference Data

### 3.1 Condition Types

| Value | Label | Description |
|-------|-------|-------------|
| `new` | New | Brand new, unused equipment |
| `used` | Used | Pre-owned equipment |
| `refurbished` | Refurbished | Restored to working condition |

### 3.2 Price Types

| Value | Display |
|-------|---------|
| `fixed` | Show actual price |
| `contact` | "Contact for Pricing" |
| `auction` | "Auction Item" |

### 3.3 Availability Status

| Value | Display | Badge Color |
|-------|---------|-------------|
| `available` | Available | Green |
| `sold` | Sold | Red/Gray |
| `pending` | Sale Pending | Yellow |
| `coming-soon` | Coming Soon | Blue |

### 3.4 Product Specifications (Common)

Standard spec keys that appear across products:

- Tonnage
- Stroke Length
- Die Size
- Production Rate
- Power Requirements
- Dimensions (L x W x H)
- Weight
- Year Manufactured
- Control System
- Condition Notes

---

## 4. Content Relationships

```
Homepage
├── Hero Slides [1..n]
├── Featured Products → Product [1..6]
└── Featured Categories → Category [1..6]

Category
├── Parent Category → Category [0..1]
└── Featured Products → Product [0..n]

Product
├── Category → Category [1]
└── Subcategories → Category [0..n]

Page
├── Parent Page → Page [0..1]
└── Sections [0..n]

Navigation
├── Items → Page | Category | URL
└── Dropdown Children → NavigationItem
```

---

## 5. Validation Rules

### 5.1 Required Fields

| Content Type | Required Fields |
|--------------|-----------------|
| Product | name, category, condition, shortDescription, description, mainImage |
| Category | name, slug |
| Page | title, slug |
| Site Settings | companyName, email, phone |

### 5.2 Constraints

- Product name: Max 100 characters
- Short description: Max 300 characters
- Slug: URL-safe characters only, auto-generated
- Gallery images: Max 10 per product
- Featured products: Max 6 on homepage
- Featured categories: Max 6 on homepage

### 5.3 Slug Generation

```
"1800 Ton Conmetal Extrusion Press" → "1800-ton-conmetal-extrusion-press"
```

Rules:
- Lowercase
- Replace spaces with hyphens
- Remove special characters
- Ensure uniqueness (append -2, -3 if duplicate)

---

## 6. CMS Structure Summary

### Cross-Platform CMS Design

**Critical Requirement:** The CMS must work equally well on Windows Desktop and iPhone.

#### Desktop (Windows) Experience
- Full sidebar navigation
- Drag-and-drop for reordering
- Large image previews
- Keyboard shortcuts
- Multi-window support

#### Mobile (iPhone) Experience
- Bottom sheet navigation
- Touch-optimized buttons (44px+)
- Swipe gestures for common actions
- Camera integration for image upload
- Portrait-optimized layouts
- Thumb-friendly form layouts

### Sanity Studio Structure

```
📁 Content
├── 📄 Homepage
├── 📁 Products
│   ├── All Products
│   ├── By Category
│   └── Hidden Products
├── 📁 Categories
├── 📁 Pages
│   ├── About
│   ├── Contact
│   ├── Equipment Wanted
│   └── Facilities
├── 📄 Site Settings
└── 📁 Contact Submissions

📁 Media
├── 📁 Product Images
├── 📁 Hero Images
├── 📁 Category Images
├── 📁 Partner Logos
└── 📁 Documents
```

### Editor Workflows

**Adding a Product:**
1. Navigate to Products → Create New
2. Fill in name, category, condition
3. Add description and upload main image
4. Set availability status
5. Save as draft → Review → Publish

**Updating Homepage:**
1. Navigate to Homepage
2. Edit hero slides (add/remove/reorder)
3. Update featured products (checkbox selection)
4. Preview changes
5. Publish

**Managing Categories:**
1. Navigate to Categories
2. Reorder via drag-and-drop
3. Edit category page content
4. Update navigation visibility

---

## 7. Migration Notes

### From Wix to New CMS

**Preserved:**
- All product data
- All images (with optimization)
- Category structure
- Page content
- SEO metadata

**URL Redirects:**
- Old Wix product URLs → New slugs
- Old category URLs → New category structure
- Maintain SEO value with 301 redirects

**Manual Migration Steps:**
1. Export Wix products to CSV
2. Download all images
3. Import to new CMS
4. Review and validate
5. Set up redirects
6. Update sitemap

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
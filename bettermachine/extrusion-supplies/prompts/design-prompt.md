# Design Prompt: Extrusion Supplies Website

## Context

You are designing a replacement website for **Extrusion Supplies**, a B2B aluminum extrusion equipment broker based in Canfield, OH. The current site is built on Wix and needs to be replaced with a modern, fast, SEO-optimized website that the owner (Tom Nentwick) can easily manage without technical knowledge.

**Current Site:** https://extrusionsupplies.com  
**Business Model:** B2B equipment catalog (no e-commerce transactions)  
**Client Tech Level:** Novice - needs WYSIWYG editing
**Industry:** Industrial aluminum extrusion equipment

## Design Goals

1. **Professional Industrial Feel** - Communicate trust, expertise, and 20+ years of experience
2. **Product-Focused** - Equipment is the hero; make browsing easy
3. **Trust Signals** - Highlight Tom's expertise, brand partnerships, and company history
4. **Easy Navigation** - Large B2B buyers need to find equipment quickly
5. **Mobile-First** - Many users browse on phones/tablets in industrial settings

## Brand Guidelines

### Color Palette
- **Primary:** #1a1a1a (Dark gray/black for headers and text)
- **Secondary:** #4a4a4a (Medium gray for secondary text)
- **Accent:** #c9a227 (Gold/amber for CTAs and links)
- **Background:** #ffffff (White) and #f5f5f5 (Light gray sections)

### Typography
- **Headings:** Inter, bold/semibold, clean industrial feel
- **Body:** System UI stack, highly readable
- **Scale:** 16px base, H1 at 48px (desktop), responsive down to 32px (mobile)

### Imagery Style
- Industrial equipment photography
- Clean backgrounds (white or industrial settings)
- Slightly desaturated, professional treatment
- High contrast for equipment detail visibility

## Required Pages

### 1. Homepage

**Sections (in order):**

1. **Header (Sticky)**
   - Logo left
   - Navigation center: Home | Browse Equipment | Contact | About
   - Phone number CTA right (click to call)
   - Mobile: Hamburger menu

2. **Hero Carousel**
   - Full-width, 60vh height
   - 3-5 featured equipment slides
   - Each slide: High-quality image + headline + subheadline + CTA button
   - Auto-advance every 5 seconds
   - Manual navigation (dots + arrows)
   - Dark gradient overlay for text readability

3. **Category Grid**
   - 6 categories in 3x2 grid (desktop), 2x3 (tablet), scrollable (mobile)
   - Categories: Extrusion Presses, Ovens & Furnaces, Pullers, Saws, CNC Machines, Die Equipment
   - Each: Icon + Category name + Background image
   - Hover: Slight scale + shadow

4. **Featured Equipment**
   - Section title: "Featured Equipment"
   - 4-6 product cards
   - Card: Image, Product name, Manufacturer, Condition badge, "Contact for Pricing" or price
   - Horizontal scroll on mobile
   - "View All Equipment" button

5. **About Section**
   - Two-column layout: Tom's photo left, text right
   - Headline: "Over 20 Years Serving the Aluminum Extrusion Industry"
   - 2-3 paragraphs about Tom's experience
   - Signature or quote
   - "Learn More About Us" button

6. **Partner Brands**
   - Section title: "Trusted Brands We Represent"
   - 6-8 partner logos in horizontal row
   - Grayscale, color on hover
   - Logos: Extral, Thermika, Ichikawa, Dunaway, etc.

7. **Contact CTA**
   - Full-width dark background
   - Headline: "Looking for Equipment?"
   - Subheadline: "Contact Tom for personalized assistance"
   - Phone and email prominently displayed
   - "Contact Us" button

8. **Footer**
   - 4 columns: Company info, Quick links, Categories, Contact
   - Social links: Facebook, LinkedIn
   - Copyright: "© 2024 Extrusion Supplies. All rights reserved."
   - Subtle map or location indicator

### 2. Product Listing Page (/browse or /equipment)

**Layout:**
- Left sidebar (desktop): Filters by category, condition, availability
- Main area: Product grid
- Mobile: Filter button opens drawer

**Features:**
- Breadcrumb: Home > Equipment
- Results count: "Showing 24 of 156 products"
- Sort dropdown: Newest, Name A-Z, Name Z-A
- Grid view / List view toggle
- Pagination or infinite scroll
- Search bar at top

**Product Card:**
- Image (4:3 aspect ratio)
- Product name
- Manufacturer badge
- Condition badge (color-coded)
- Short description (2 lines)
- Availability badge
- "Contact About This Item" button

### 3. Product Detail Page

**Layout:**
- Two-column: Gallery left (60%), Info right (40%)
- Mobile: Stacked

**Left Column:**
- Main image (large)
- Thumbnail gallery below (5-10 images)
- Image zoom on click
- Lightbox option

**Right Column:**
- Product name (H1)
- Manufacturer + Model
- Condition badge (large)
- Availability status
- Short description
- Full description (rich text)
- Specifications table
- "Contact Tom About This Equipment" CTA button (prominent)
- Email link
- Phone click-to-call
- Share buttons

**Below Fold:**
- Related equipment (3-4 similar items)
- Contact form (optional inline)

### 4. Contact Page

**Layout:**
- Two-column: Form left, Contact info right

**Left:**
- Form fields: Name, Company, Email, Phone, Equipment Interest (dropdown), Message
- Submit button
- Success message after submit

**Right:**
- Address with map embed
- Phone (click to call)
- Email (mailto link)
- Hours of operation
- Social links

### 5. About Page

**Sections:**
1. Hero with Tom's photo and tagline
2. Tom's full bio (500+ words)
3. Company history/timeline
4. Facility photos (if available)
5. Industry affiliations/partnerships
6. Contact CTA

## Design Principles

1. **Clarity First** - Industrial buyers need to quickly understand what equipment is available
2. **Trust Through Detail** - High-quality images, detailed specs, and Tom's personal presence
3. **Mobile-First** - Many users will be on mobile devices in warehouses/facilities
4. **Speed** - Fast loading is critical for SEO and user experience
5. **Scannable** - Clear hierarchy, use of badges and labels, easy-to-scan product grids

## Interactions & Animations

**Keep it subtle and professional:**
- Links: Color change on hover (150ms ease)
- Buttons: Background darken + slight lift (200ms ease)
- Cards: Shadow increase + lift on hover (200ms ease)
- Images: Slight scale (1.02) with overflow hidden on hover
- Page transitions: Subtle fade (200ms)
- Scroll: Smooth scroll behavior

**Avoid:**
- Flashy animations
- Auto-playing video
- Parallax effects
- Heavy motion

## Responsive Behavior

**Desktop (1280px+):**
- Full navigation
- Multi-column layouts
- Sidebar filters

**Tablet (768px - 1279px):**
- Hamburger menu
- 2-column grids
- Stacked layouts

**Mobile (< 768px):**
- Single column
- Touch-friendly targets (44px minimum)
- Swipeable carousels
- Sticky header with click-to-call

## Design Deliverables Expected

1. **Figma File** with:
   - All page designs (desktop + mobile)
   - Component library
   - Design system documentation
   - Prototype interactions

2. **Assets:**
   - All exported images
   - Icon set recommendations
   - Logo variations

3. **Specs:**
   - Typography scale
   - Spacing system
   - Color palette (hex codes)
   - Component measurements

## CMS Design Considerations

**Remember:** Tom needs to manage this himself

- Homepage sections should be clearly editable blocks
- Product forms should be straightforward
- Image uploads should show preview
- Status changes (published/hidden) should be obvious
- Preview before publish is essential
- Undo/redo capability

## Inspiration Sites

- Modern manufacturing sites (Caterpillar, Siemens)
- Industrial equipment marketplaces
- Clean B2B SaaS sites (for UX patterns)
- Avoid: E-commerce consumer sites (too flashy), Pure corporate sites (too generic)

## Questions to Consider

1. How do we best showcase large industrial equipment in a clean way?
2. What's the right balance between Tom's personal brand and the company?
3. How can we make 100+ products feel browsable without being overwhelming?
4. What trust signals matter most to B2B equipment buyers?
5. How do we handle equipment that's sold (archive vs. show as sold)?

---

**Output:** Design mockups for all 5 key pages, component library, and design system documentation in Figma or similar tool.
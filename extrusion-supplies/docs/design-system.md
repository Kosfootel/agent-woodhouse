# Extrusion Supplies - Design System

## 1. Brand Identity

### 1.1 Brand Overview

**Company:** Extrusion Supplies  
**Industry:** Industrial Aluminum Extrusion Equipment  
**Brand Personality:** Established, Trustworthy, Professional, Industrial  
**Years in Business:** 20+ years

### 1.2 Brand Values
- Reliability
- Industry Expertise
- Personal Service (Tom's direct involvement)
- Quality Equipment
- Long-term Relationships

## 2. Color Palette

### 2.1 Primary Colors

Based on analysis of current site:

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-primary` | `#1a1a1a` | Headings, primary text, buttons |
| `--color-primary-dark` | `#000000` | Hover states, emphasis |
| `--color-secondary` | `#4a4a4a` | Secondary text, borders |
| `--color-accent` | `#c9a227` | Links, highlights, CTAs (gold/amber from current site) |
| `--color-accent-dark` | `#a08020` | Accent hover states |

### 2.2 Neutral Colors

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-white` | `#ffffff` | Backgrounds, cards |
| `--color-gray-100` | `#f5f5f5` | Section backgrounds |
| `--color-gray-200` | `#e5e5e5` | Borders, dividers |
| `--color-gray-300` | `#d4d4d4` | Disabled states |
| `--color-gray-500` | `#737373` | Secondary text |
| `--color-gray-700` | `#404040` | Body text |
| `--color-gray-900` | `#171717` | Headings |

### 2.3 Semantic Colors

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-success` | `#22c55e` | Success states, available |
| `--color-warning` | `#f59e0b` | Pending, featured |
| `--color-error` | `#ef4444` | Errors, sold |
| `--color-info` | `#3b82f6` | Information |

## 3. Typography

### 3.1 Font Families

**Primary (Headings):** Inter or similar industrial sans-serif
- Clean, modern, professional
- Good for technical/industrial content

**Secondary (Body):** System UI / Inter
- Highly readable
- Good performance (system font stack)

```css
/* Font Stack */
--font-heading: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### 3.2 Type Scale

| Style | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| H1 | 48px / 3rem | 700 | 1.1 | -0.02em | Hero headlines |
| H2 | 36px / 2.25rem | 600 | 1.2 | -0.01em | Section titles |
| H3 | 28px / 1.75rem | 600 | 1.3 | 0 | Card titles, subsections |
| H4 | 24px / 1.5rem | 600 | 1.4 | 0 | Feature titles |
| H5 | 20px / 1.25rem | 600 | 1.4 | 0 | Small headings |
| H6 | 18px / 1.125rem | 600 | 1.4 | 0 | Labels |
| Body Large | 18px / 1.125rem | 400 | 1.6 | 0 | Intro paragraphs |
| Body | 16px / 1rem | 400 | 1.6 | 0 | Main content |
| Body Small | 14px / 0.875rem | 400 | 1.5 | 0 | Secondary text |
| Caption | 12px / 0.75rem | 400 | 1.4 | 0.01em | Meta text |

### 3.3 Mobile Type Scale

| Style | Mobile Size |
|-------|-------------|
| H1 | 32px |
| H2 | 28px |
| H3 | 24px |
| H4 | 20px |
| H5 | 18px |
| Body | 16px |

## 4. Spacing System

### 4.1 Base Unit

Base unit: **8px**

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight spacing |
| `--space-2` | 8px | Base unit |
| `--space-3` | 12px | Small gaps |
| `--space-4` | 16px | Standard padding |
| `--space-6` | 24px | Component gaps |
| `--space-8` | 32px | Section spacing |
| `--space-12` | 48px | Large sections |
| `--space-16` | 64px | Hero spacing |
| `--space-20` | 80px | Major sections |
| `--space-24` | 96px | Page sections |

### 4.2 Container Widths

| Token | Value | Usage |
|-------|-------|-------|
| `--container-sm` | 640px | Narrow content |
| `--container-md` | 768px | Medium content |
| `--container-lg` | 1024px | Standard content |
| `--container-xl` | 1280px | Wide content |
| `--container-full` | 100% | Full width sections |

### 4.3 Grid System

- 12-column grid
- 24px gutters (desktop)
- 16px gutters (tablet)
- 12px gutters (mobile)

## 5. Components

### 5.1 Buttons

**Primary Button:**
- Background: `--color-accent`
- Text: `--color-white`
- Padding: 16px 32px
- Border-radius: 4px
- Font-weight: 600
- Hover: `--color-accent-dark`

**Secondary Button:**
- Background: transparent
- Border: 2px solid `--color-primary`
- Text: `--color-primary`
- Hover: `--color-primary` bg, white text

**Ghost Button:**
- Background: transparent
- Text: `--color-accent`
- Hover: Light background tint

### 5.2 Cards

**Product Card:**
- Background: white
- Border: 1px solid `--color-gray-200`
- Border-radius: 8px
- Shadow: 0 2px 8px rgba(0,0,0,0.08)
- Hover shadow: 0 4px 16px rgba(0,0,0,0.12)
- Image aspect ratio: 4:3
- Padding: 16px

**Content Card:**
- Background: `--color-gray-100`
- Border-radius: 8px
- Padding: 24px

### 5.3 Forms

**Input Fields:**
- Border: 1px solid `--color-gray-300`
- Border-radius: 4px
- Padding: 12px 16px
- Focus: Border `--color-accent`
- Error: Border `--color-error`

**Labels:**
- Font-weight: 500
- Margin-bottom: 4px
- Color: `--color-gray-700`

### 5.4 Navigation

**Header:**
- Height: 72px (desktop), 64px (mobile)
- Background: white
- Border-bottom: 1px solid `--color-gray-200`
- Position: Sticky on scroll
- Z-index: 50

**Mobile Menu:**
- Full-screen overlay
- Slide-in from right
- Close button top-right

### 5.5 Hero Section

**Hero Carousel:**
- Height: 60vh (min 400px, max 600px)
- Overlay: Linear gradient for text readability
- Dots navigation bottom
- Auto-advance: 5 seconds
- Manual navigation arrows

**Hero Content:**
- Centered or left-aligned
- Max-width: 600px
- Text shadow for contrast

## 6. Layout Patterns

### 6.1 Homepage Sections

1. **Header** (sticky)
2. **Hero Carousel** (full-width)
3. **Category Grid** (6 items, 3x2 grid)
4. **Featured Equipment** (4-6 items, horizontal scroll or grid)
5. **About/Founder** (2-column: image + text)
6. **Partner Logos** (horizontal scroll/grid)
7. **Contact CTA** (full-width background)
8. **Footer**

### 6.2 Product Listing Page

- Sidebar filters (desktop) / Top filters (mobile)
- Breadcrumb navigation
- Sort dropdown
- Grid view (default) / List view toggle
- Pagination or infinite scroll
- 3-column grid (desktop), 2-column (tablet), 1-column (mobile)

### 6.3 Product Detail Page

- Breadcrumb navigation
- Image gallery (left side)
- Product info (right side)
- Contact CTA prominent
- Specifications table
- Related products (bottom)

## 7. Imagery Guidelines

### 7.1 Image Specifications

**Product Images:**
- Aspect ratio: 4:3 (recommended)
- Minimum resolution: 800x600px
- Format: WebP with JPEG fallback
- Max file size: 200KB per image
- Background: Clean, white or transparent preferred

**Hero Images:**
- Aspect ratio: 16:9 or 21:9
- Minimum resolution: 1920x1080px
- Subject: Equipment in industrial setting

**Founder/Team Photos:**
- Aspect ratio: 3:4 or 1:1
- Professional headshots
- Consistent background

### 7.2 Image Treatment

- Slight contrast boost
- Consistent color grading (slightly desaturated, industrial feel)
- Optional subtle vignette
- Consistent shadows/lighting

## 8. Animations & Interactions

### 8.1 Micro-interactions

**Hover States:**
- Links: Color change + 150ms transition
- Buttons: Background darken + 200ms transition
- Cards: Shadow increase + slight lift (translateY -4px)
- Images: Slight scale (1.02) with overflow hidden

**Focus States:**
- Outline: 2px solid `--color-accent`
- Outline-offset: 2px

### 8.2 Page Transitions

- Subtle fade-in on page load (200ms)
- Smooth scroll behavior

### 8.3 Loading States

- Skeleton screens for product grids
- Spinner for form submissions
- Image lazy loading with blur-up placeholder

## 9. Responsive Breakpoints

| Breakpoint | Width | Target |
|------------|-------|--------|
| Mobile | < 640px | Phones |
| Tablet | 640px - 1024px | Tablets, small laptops |
| Desktop | 1024px - 1280px | Laptops |
| Large | > 1280px | Desktops |

## 10. Accessibility Guidelines

### 10.1 Color Contrast

- Text on backgrounds: Minimum 4.5:1 ratio
- Large text (18px+): Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 ratio

### 10.2 Focus Management

- Visible focus indicators on all interactive elements
- Skip-to-content link
- Logical tab order

### 10.3 Screen Reader Support

- Semantic HTML structure
- ARIA labels where needed
- Alt text for all images
- Descriptive link text

## 11. Component Library

### Recommended Structure

```
components/
├── ui/
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   ├── Select.tsx
│   ├── Modal.tsx
│   └── Icon.tsx
├── layout/
│   ├── Header.tsx
│   ├── Footer.tsx
│   ├── Container.tsx
│   └── Grid.tsx
├── sections/
│   ├── Hero.tsx
│   ├── ProductGrid.tsx
│   ├── CategoryGrid.tsx
│   └── ContactCTA.tsx
└── product/
    ├── ProductCard.tsx
    ├── ProductGallery.tsx
    └── ProductSpecs.tsx
```

## 12. Figma/Design File Structure

Recommended layer organization:

```
📁 Extrusion Supplies Website
├── 📄 Cover
├── 📄 Design System
│   ├── Colors
│   ├── Typography
│   ├── Components
│   └── Spacing
├── 📄 Desktop
│   ├── Homepage
│   ├── Product Listing
│   ├── Product Detail
│   ├── About
│   └── Contact
├── 📄 Mobile
│   ├── Homepage
│   ├── Product Listing
│   ├── Product Detail
│   ├── About
│   └── Contact
└── 📄 Components
    └── All reusable components
```

## 13. Assets

### Logo Requirements

- **Formats:** SVG (primary), PNG (fallback)
- **Sizes:**
  - Favicon: 32x32px, 180x180px (apple-touch)
  - Header: Height 40px
  - Footer: Height 60px
- **Color versions:** Full color, white (for dark backgrounds)

### Icon System

**Recommended:** Lucide React or Heroicons
- Consistent 24x24px base
- 1.5px stroke width
- Industrial/technical feel

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
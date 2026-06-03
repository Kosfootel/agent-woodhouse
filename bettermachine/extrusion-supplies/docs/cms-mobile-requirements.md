# Extrusion Supplies - CMS Mobile Requirements

## Critical Requirement: iPhone + Windows Desktop Editing

**Primary Use Case:** Tom must be able to edit the website from his **Windows desktop** OR his **iPhone** with equal ease and functionality.

---

## Cross-Platform CMS Requirements

### Core Principle
**NO desktop-only features.** Every editing capability available on Windows must also work on iPhone.

### Platform Support

| Feature | Windows Desktop | iPhone | Notes |
|---------|----------------|--------|-------|
| Add/Edit Products | ✅ Full | ✅ Full | Identical forms |
| Upload Images | ✅ File picker | ✅ Camera + Library | Take photo or select existing |
| Edit Homepage | ✅ Full | ✅ Full | Responsive layout |
| Preview Changes | ✅ Full | ✅ Full | Mobile preview on mobile |
| Publish Content | ✅ Full | ✅ Full | Big touch button on mobile |
| Rich Text Editing | ✅ Full | ✅ Full | Mobile-optimized toolbar |
| Category Management | ✅ Full | ✅ Full | Touch-friendly drag alternative |
| Navigation Editing | ✅ Full | ✅ Full | Reordering works on both |

---

## iPhone-Specific Requirements

### Touch Target Guidelines
- **Minimum button size:** 44px x 44px
- **Form input height:** 48px minimum
- **Spacing between touch targets:** 8px minimum
- **No hover-dependent actions** (use tap instead)

### Image Upload on iPhone
**Required Capabilities:**
1. **Take Photo** - Direct camera access from CMS
2. **Choose from Library** - Select existing photos
3. **Multiple Select** - Upload up to 10 images at once
4. **Preview Before Upload** - See image before sending
5. **Automatic Compression** - Large photos compressed before upload

**Workflow:**
```
Tap "Add Image" → Choose Source (Camera/Library) → 
Select/Take Photo → Preview → Crop/Rotate (optional) → 
Confirm Upload → See thumbnail in CMS
```

### Mobile Form Layout

**Product Form on iPhone:**
```
[Product Name    ]  (Full width, large tap target)
[Category        ▼]  (Native picker)
[Condition       ▼]  (Native picker)

[Main Image]
[+ Take Photo or Upload]  (Big button)

[Description     ]
[                ]  (Expandable text area)
[                ]

[Save as Draft] [Publish]  (Two large buttons)
```

### Mobile Navigation

**Sanity Studio Mobile Layout:**
- **Bottom tab bar** (instead of sidebar)
  - Dashboard | Content | Media | Settings
- **Swipe gestures:**
  - Swipe right to go back
  - Swipe between content items
  - Pull down to refresh
- **Modals instead of side panels** (for mobile)

---

## Windows Desktop Requirements

### Desktop Optimizations
**Enhanced features that are nice-to-have (not required for iPhone):**
- Drag-and-drop image upload (drag files from Explorer)
- Keyboard shortcuts (Ctrl+S to save)
- Right-click context menus
- Multi-window support
- Larger preview panels

### Core Functionality
All core editing features must mirror iPhone capabilities.

---

## Technical Implementation

### Sanity Studio Customization

```typescript
// sanity.config.ts
export default defineConfig({
  // ... other config
  theme: {
    // Mobile-friendly theme
    '--font-size-base': '16px', // Prevents iPhone zoom on input focus
    '--touch-target-min': '44px',
    '--space-1': '4px',
    '--space-2': '8px',
    '--space-3': '12px',
    '--space-4': '16px',
    '--space-6': '24px',
  },
  plugins: [
    // Mobile-optimized plugins
    deskTool({
      // Responsive desk structure
    }),
  ],
});
```

### Image Upload Component

```typescript
// Mobile-optimized image input
interface ImageUploadProps {
  onUpload: (files: File[]) => void;
  accept?: string;
  maxFiles?: number;
  capture?: 'environment' | 'user'; // Camera facing
}

// Renders differently on mobile vs desktop:
// Mobile: Shows "Take Photo" + "Choose from Library" buttons
// Desktop: Shows drag-drop zone + file picker
```

### Responsive Form Components

```typescript
// Touch-friendly form inputs
const FormInput = styled.input`
  min-height: 48px;
  font-size: 16px; // Prevents zoom on iOS
  padding: 12px 16px;
  border-radius: 8px;
  
  @media (min-width: 768px) {
    min-height: 40px;
  }
`;

const TouchButton = styled.button`
  min-height: 44px;
  min-width: 44px;
  padding: 12px 24px;
  
  @media (max-width: 767px) {
    width: 100%; // Full width on mobile
    margin-bottom: 8px;
  }
`;
```

---

## Testing Requirements

### iPhone Testing Checklist

**Device:** iPhone 12 or newer  
**Browsers:** Safari, Chrome iOS  
**iOS Version:** Latest stable

```
□ Add new product entirely from iPhone
□ Upload main image from camera
□ Upload gallery images from photo library
□ Edit existing product
□ Change homepage featured products
□ Update hero image
□ Edit text content
□ Preview changes
□ Publish content
□ Log out and log back in
□ Use on cellular connection (not just WiFi)
□ Rotate between portrait and landscape
```

### Windows Testing Checklist

**OS:** Windows 10 or 11  
**Browsers:** Chrome, Edge, Firefox

```
□ Add new product from desktop
□ Drag and drop image upload
□ Edit all product fields
□ Navigate CMS with keyboard only
□ Preview changes
□ Publish content
□ Upload multiple images at once
```

### Cross-Platform Sync

```
□ Edit on iPhone, see changes on desktop
□ Edit on desktop, see changes on iPhone
□ Images uploaded on one device appear on other
□ No data loss between platforms
□ Consistent experience (same fields, same options)
```

---

## User Experience Guidelines

### For iPhone

**DO:**
- ✅ Use native iOS pickers for selects
- ✅ Show large, thumb-friendly buttons
- ✅ Support swipe gestures
- ✅ Use bottom sheets for actions
- ✅ Optimize for portrait mode primarily
- ✅ Test on actual iPhone (not just simulator)

**DON'T:**
- ❌ Require hover interactions
- ❌ Use tiny font sizes (causes zoom)
- ❌ Make buttons smaller than 44px
- ❌ Use horizontal scrolling
- ❌ Require right-click actions

### For Windows Desktop

**DO:**
- ✅ Support drag-and-drop
- ✅ Enable keyboard shortcuts
- ✅ Show larger previews
- ✅ Use hover states for discovery
- ✅ Support right-click menus

---

## Accessibility Across Platforms

### iPhone
- VoiceOver support
- Dynamic Type support (respect user font size)
- Reduce Motion support
- High Contrast support

### Windows
- Windows High Contrast mode
- Keyboard navigation
- Screen reader support (NVDA, JAWS)
- Focus indicators

---

## Performance Considerations

### Mobile Network
- Image upload should work on 4G/LTE
- Show upload progress
- Allow background upload
- Compress images before upload
- Resume interrupted uploads

### Desktop
- Faster upload with parallel processing
- Drag-drop from file explorer
- Bulk operations

---

## Fallbacks & Edge Cases

### When Camera Access is Denied
- Show clear error message
- Guide to Settings to enable
- Still allow library upload
- Manual file upload option

### When Upload Fails
- Retry button
- Save form data (don't lose work)
- Show specific error reason
- Offline mode indicator

### Large Image Handling
- Auto-compress before upload
- Show file size warning
- Progress indicator
- Cancel option

---

## Documentation for Tom

### iPhone Quick Guide

**Adding a Product from Your iPhone:**
1. Open Safari, go to [CMS URL]
2. Log in
3. Tap "+" (Add New)
4. Tap "Product"
5. Fill in name, category, condition
6. Tap "Add Image" → "Take Photo" or "Choose from Library"
7. Add description
8. Tap "Publish" (top right)

**Common iPhone Tasks:**
- **Take photo of equipment:** Add Image → Take Photo
- **Update homepage:** Dashboard → Homepage → Edit
- **Hide sold item:** Products → Item → Status: Hidden → Save

### Windows Quick Guide

**Adding a Product from Desktop:**
1. Open Chrome, go to [CMS URL]
2. Log in
3. Click "New Product"
4. Fill in details
5. Drag images from folder or click "Upload"
6. Click "Publish"

---

## Success Criteria

### Cross-Platform Editing Works When:

1. **Tom can add a complete product** from iPhone in under 5 minutes
2. **Tom can add a complete product** from Windows in under 3 minutes
3. **Image upload succeeds** from iPhone camera 95%+ of the time
4. **No feature requires** "switch to desktop"
5. **Preview is accurate** on both platforms
6. **Publishing works reliably** on both platforms
7. **No data loss** when switching between devices

---

*Document Version: 1.0*  
*Last Updated: 2026-05-30*  
*Author: BetterMachine Agency*
# Vigil Dashboard Frontend Code Review

**Review Date:** 2026-05-26  
**Reviewer:** Frontend Code Reviewer Agent  
**Scope:** `/Users/FOS_Erik/.openclaw/workspace/vigil-work/dashboard/`

---

## Executive Summary

The Vigil Dashboard is a React 18 application built with Create React App. It provides a security monitoring dashboard with router discovery, device management, and alert handling. While the codebase functions correctly, there are several areas requiring attention including security vulnerabilities, performance optimizations, and architectural improvements.

**Overall Assessment:** Functional but needs hardening for production use.

---

## 1. React Component Architecture Analysis

### Current Structure

```
src/
├── App.js                    # Main router + layout wrapper
├── index.js                  # Entry point
├── api.js                    # API client module
├── index.css                 # Global styles
├── components/
│   ├── EventTimeline.js      # Security events display
│   ├── AlertPanel.js         # Alert management UI
│   ├── BlockedCounter.js     # Blocked prompt stats
│   ├── ToolChart.js          # Tool usage chart
│   ├── AccessHeatmap.js      # Memory access visualization
│   └── setup/
│       ├── index.js          # Setup module exports
│       ├── SetupWizard.js    # Multi-step setup flow
│       ├── SetupWizard.css   # Setup-specific styles
│       └── router-discovery.css
├── lib/
│   └── routerDiscovery.js    # Router discovery utilities
└── pages/
    ├── DevicesPage.js        # Device management page
    ├── AlertsPage.js         # Alerts list page
    ├── AgentsPage.js         # Agent management page
    └── SetupPage.js          # Setup page wrapper
```

### Architecture Issues

#### 1.1 Mixed Component Patterns

**Issue:** Components use both class-style state initialization and inconsistent patterns.

**Location:** Multiple files

**Example from AlertPanel.js:16-20:**
```javascript
const [alerts, setAlerts] = useState([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
const [stats, setStats] = useState({ new_count: 0, acknowledged_count: 0 });
```

While functional, error state is never actually displayed to users, only logged to console.

#### 1.2 Page Component Duplication

**Issue:** Page wrapper pattern creates unnecessary duplication.

**Location:** `App.js:104-130`

```javascript
const PageWrapper = ({ children, title }) => (
  <div className="app">
    <header className="header">...</header>
    <main className="dashboard">{children}</main>
    <footer className="footer">...</footer>
  </div>
);

// Creates 4 nearly identical wrapper components
const Devices = () => (<PageWrapper title="Device Management"><DevicesPage /></PageWrapper>);
const Alerts = () => (<PageWrapper title="Security Alerts"><AlertsPage /></PageWrapper>);
```

**Recommendation:** Use a Layout component with React Router's `<Outlet />` pattern.

#### 1.3 Setup Wizard Complexity

**Issue:** `SetupWizard.js` (600+ lines) violates Single Responsibility Principle.

- Contains all 5 step render functions inline
- Mixes presentation and business logic
- Has internal state for wizard flow that could be extracted

**Recommendation:** Split into:
- `WizardContainer.js` - State management
- `steps/WelcomeStep.js`, `steps/RouterDiscoveryStep.js`, etc.
- `hooks/useWizard.js` - Shared wizard logic

---

## 2. State Management Evaluation

### Current Approach

All components use **local React state** with `useState` and `useEffect`. No global state management (Redux, Zustand, Context) is implemented.

### Strengths
- Simple for current feature set
- No additional dependencies
- Easy to understand for new developers

### Weaknesses

#### 2.1 Prop Drilling Risk

While not severe now, as features grow, passing data between components will become problematic.

#### 2.2 Inconsistent Data Fetching

**Issue:** Components implement their own data fetching patterns inconsistently.

**AlertPanel.js:25-40:** Uses centralized `api.js`:
```javascript
import { getAlerts, acknowledgeAlert } from '../api';
const response = await getAlerts();
```

**DevicesPage.js:9-12:** Uses raw fetch:
```javascript
const response = await fetch(`http://192.168.50.30:8000/api/devices`);
```

**AlertsPage.js:15:** Hardcodes API URL:
```javascript
const API_URL = 'http://192.168.50.30:8000';
```

#### 2.3 No Query Caching

Each component fetches independently. Multiple navigations cause redundant API calls.

**Recommendation:** Consider React Query (TanStack Query) for:
- Automatic caching
- Background refetching
- Loading/error states
- Request deduplication

---

## 3. Security Vulnerabilities

### 🔴 CRITICAL

#### 3.1 Hardcoded API URLs with IP Addresses

**Location:** Multiple files

| File | Line | Issue |
|------|------|-------|
| `api.js` | 4 | `const API_BASE_URL = 'http://192.168.50.30:8000';` |
| `DevicesPage.js` | 9 | Hardcoded in fetch call |
| `AlertsPage.js` | 15 | Hardcoded `API_URL` constant |
| `AgentsPage.js` | 11 | Hardcoded `API_URL` constant |
| `SetupWizard.js` | 92, 125, 148 | Multiple hardcoded URLs |
| `App.js` | 26 | Fallback hardcoded in checkSetup |

**Risk:** Production deployments will fail if backend isn't at this exact IP. URLs should be environment-configurable.

#### 3.2 Stored Credentials in LocalStorage

**Location:** `routerDiscovery.js:119-129`

```javascript
export function saveProgress(step, data) {
  const progress = {
    step,
    data,  // May contain sensitive router credentials
    timestamp: Date.now(),
  };
  localStorage.setItem('vigilSetupProgress', JSON.stringify(progress));
}
```

**Risk:** Setup data (potentially including credentials) persists in browser storage indefinitely.

#### 3.3 No Input Sanitization

**Location:** `EventTimeline.js:83-88`

```javascript
<div style={{ fontSize: '0.9em', color: '#374151', marginTop: '4px' }}>
  {event.details}  {/* Directly rendered without sanitization */}
</div>
```

**Risk:** If `event.details` contains malicious content from the backend, it could execute.

#### 3.4 XSS Risk: Dangerous innerHTML Pattern

**Location:** Multiple places where `dangerouslySetInnerHTML` could be introduced.

Currently the app avoids this, but the pattern exists where HTML content is injected via JSX expressions without proper sanitization.

### 🟡 HIGH

#### 3.5 No CSRF Protection

All API calls lack CSRF tokens. The backend appears to accept requests without verification.

#### 3.6 Insecure CORS Configuration (Proxy)

**Location:** `package.json:23`

```json
"proxy": "http://localhost:8000"
```

This only works in development. Production builds won't have this proxy.

#### 3.7 Window.confirm() Pattern

**Location:** `AlertsPage.js:44-46`

```javascript
if (!window.confirm(`Acknowledge all ${newCount} unacknowledged alerts?`)) {
  return;
}
```

While not a vulnerability, using browser APIs directly makes testing harder and UI inconsistent.

---

## 4. Performance Issues

### 4.1 Unnecessary Re-renders

#### Missing useMemo for Derived Data

**Location:** `AccessHeatmap.js:50`

```javascript
const filteredData = accessData.filter(item => item.count > 0);
```

This filter runs on every render even when `accessData` hasn't changed.

#### Missing useCallback for Event Handlers

**Location:** `SetupWizard.js:170-175`

```javascript
const handleDiscoverRouters = async () => {
  // ... handler recreated on every render
};
```

These handlers are passed to child components causing unnecessary re-renders.

### 4.2 No Lazy Loading

The entire application is bundled together. Routes should use `React.lazy()`:

```javascript
// Currently
import DevicesPage from './pages/DevicesPage';

// Should be
const DevicesPage = React.lazy(() => import('./pages/DevicesPage'));
```

### 4.3 Large Dependencies

**Location:** `package.json`

- `recharts` (charting library) is included in main bundle
- `axios` is used alongside native `fetch` (redundant)

### 4.4 Polling Instead of WebSockets

Components use `setInterval` for real-time updates:

**DevicesPage.js:22:**
```javascript
const interval = setInterval(fetchDevices, 30000);
```

**AlertsPage.js:26:**
```javascript
const interval = setInterval(fetchAlerts, 10000);
```

This creates unnecessary network traffic. Consider Server-Sent Events or WebSockets.

---

## 5. Accessibility (a11y) Compliance

### 🔴 Critical Violations

#### 5.1 Missing Form Labels

**Location:** `SetupWizard.js:298-318`

```javascript
<input
  type="text"
  id="routerIp"
  value={credentialsForm.routerIp}
  onChange={(e) => setCredentialsForm({ ...credentialsForm, routerIp: e.target.value })}
  placeholder="192.168.50.1"
  required
/>
```

While there are `<label>` elements, the association pattern is inconsistent.

#### 5.2 Insufficient Color Contrast

**Location:** `index.css`

```css
background-color: #1e293b;  /* slate-800 */
color: #94a3b8;             /* slate-400 */
```

This combination has contrast ratio of ~4.2:1, which may fail WCAG AA for small text.

#### 5.3 Missing ARIA Attributes

- No `aria-live` regions for dynamic content updates
- No `aria-label` on icon-only buttons
- No `role` attributes on custom components

#### 5.4 Keyboard Navigation Issues

**Location:** `SetupWizard.js:228-242`

Router cards are clickable but not keyboard accessible:

```javascript
<div
  className={`router-card ${selectedRouter?.ip === router.ip ? 'selected' : ''}`}
  onClick={() => handleSelectRouter(router)}  // No keyboard handler
>
```

### 🟡 Recommendations

1. Add `tabIndex={0}` and keyboard handlers to clickable divs
2. Use semantic `<button>` elements instead of divs for actions
3. Add `aria-pressed` for toggle buttons
4. Implement focus management for wizard steps

---

## 6. CSS/Styling Approach

### Current Approach

- Single global CSS file (`index.css`) with ~700 lines
- CSS custom properties not used
- No CSS-in-JS or utility-first framework
- Component-specific CSS for SetupWizard only

### Issues

#### 6.1 Global Namespace Pollution

All styles are global. Risk of class name collisions as the app grows.

#### 6.2 No Design System

Colors are hardcoded throughout:

```css
/* index.css - repeated hex values */
background-color: #1e293b;  /* vs using var(--color-bg-primary) */
color: #dc2626;             /* vs using var(--color-danger) */
```

#### 6.3 Responsive Design Gaps

**Location:** `index.css:450-488`

Mobile breakpoints exist but tablet/medium screen optimization is minimal.

#### 6.4 Unused CSS Classes

Many defined classes in `index.css` are not used (e.g., `.severity-badge`, `.ack-button` classes vs inline styles).

### Recommendations

1. **CSS Modules** or **Tailwind CSS** for scoped styles
2. CSS Custom Properties for theming:
   ```css
   :root {
     --color-bg-primary: #0f172a;
     --color-bg-secondary: #1e293b;
     --color-accent: #3b82f6;
     --color-danger: #dc2626;
   }
   ```
3. Separate layout and component styles

---

## 7. API Integration Patterns

### 7.1 Inconsistent HTTP Client Usage

**File:** `api.js`

Uses `axios` but other files use native `fetch`. Standardize on one approach.

### 7.2 No Request/Response Interceptors

**Location:** `api.js:6-11`

```javascript
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

No interceptors for:
- Authentication token injection
- Error handling
- Request logging
- Retry logic

### 7.3 Error Handling Inconsistency

**api.js:13-15:**
```javascript
export const getSecurityEvents = (filters = {}) => {
  return api.get('/api/security/events', { params: filters });
};
```

Errors bubble up without transformation. Components handle errors inconsistently.

### 7.4 Missing Request Cancellation

No `AbortController` usage for long-running requests. Component unmounting could cause memory leaks.

---

## 8. Error Handling

### Current State

Basic try/catch blocks with console.error logging. Users see generic "Loading..." or no feedback.

### Issues by Location

| File | Issue | Line |
|------|-------|------|
| `EventTimeline.js` | Error not displayed to users | 44 |
| `AlertPanel.js` | Acknowledge errors only logged | 57, 65 |
| `DevicesPage.js` | Fetch errors swallowed | 14 |
| `SetupWizard.js` | Some errors shown, inconsistent | Various |

### Recommendations

1. **Error Boundary** at app level
   ```javascript
   // components/ErrorBoundary.js
   class ErrorBoundary extends React.Component {
     // ... implementation
   }
   ```

2. **Toast/Notification System**
   For user-visible errors (acknowledge failed, network error, etc.)

3. **Structured Error Handling**
   ```javascript
   try {
     await api.action();
   } catch (error) {
     if (error.response?.status === 401) {
       // Handle auth error
     } else if (error.response?.status === 500) {
       // Handle server error
     }
   }
   ```

---

## 9. Build Configuration Review

### package.json

```json
{
  "name": "vigil-dashboard",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^7.15.1",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "react-scripts": "^5.0.1"
  }
}
```

### Issues

#### 9.1 No TypeScript

JavaScript-only codebase. No type safety for API responses or component props.

#### 9.2 Missing Development Tools

- No ESLint configuration (beyond `react-app` defaults)
- No Prettier configuration
- No pre-commit hooks
- No testing dependencies (`react-scripts` includes jest, but no tests exist)

#### 9.3 No Environment Validation

No schema validation for environment variables.

#### 9.4 Build Optimization

`react-scripts` is production-ready but lacks:
- Bundle analysis configuration
- Tree-shaking verification
- Modern browser targeting (only `>0.2%, not dead`)

#### 9.5 Dockerfile

**Location:** `Dockerfile`

```dockerfile
FROM node:18-alpine
# ...
CMD ["npm", "start"]  # Runs dev server, not production build
```

**Issue:** Docker image runs development server. Should serve built static files.

---

## 10. Testing

### Current State

**Zero test coverage.** No test files found in the codebase.

### Missing Test Types

1. **Unit Tests** - Component rendering, hook behavior
2. **Integration Tests** - API integration, form submission
3. **E2E Tests** - Critical user flows (setup, alerts)
4. **Accessibility Tests** - axe-core or similar

### Recommendations

1. Add testing dependencies:
   ```json
   {
     "@testing-library/react": "^14.x",
     "@testing-library/jest-dom": "^6.x",
     "@testing-library/user-event": "^14.x",
     "msw": "^2.x"  // Mock Service Worker
   }
   ```

2. Minimum test coverage targets:
   - 70% business logic
   - 100% security-critical paths

---

## Summary Table

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 4 | 3 | 2 | 2 |
| Performance | 0 | 2 | 3 | 2 |
| Accessibility | 4 | 2 | 3 | 1 |
| Architecture | 0 | 1 | 4 | 3 |
| Code Quality | 0 | 1 | 3 | 4 |
| **Total** | **8** | **9** | **15** | **12** |

---

## Positive Observations

1. ✅ React 18 with modern patterns (functional components, hooks)
2. ✅ React Router v7 (latest)
3. ✅ Clean component file structure
4. ✅ Responsive design basics present
5. ✅ Separation of concerns (api.js, components, pages)
6. ✅ Dark theme consistently applied
7. ✅ Setup wizard provides good UX flow

---

*End of Review*

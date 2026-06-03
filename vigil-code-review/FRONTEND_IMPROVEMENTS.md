# Vigil Dashboard Frontend Improvements

**Prioritized by Impact** - High-impact items should be addressed first.

---

## 🔴 P0 - Critical (Security & Production Blockers)

### 1. Environment-Based API Configuration
**Impact:** Blocks production deployment, exposes internal IPs  
**Effort:** Small

Replace all hardcoded API URLs with environment variables:

```javascript
// api.js - BEFORE
const API_BASE_URL = 'http://192.168.50.30:8000';

// api.js - AFTER  
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';
```

**Files to modify:**
- `api.js` (line 4)
- `DevicesPage.js` (line 9)
- `AlertsPage.js` (line 15)
- `AgentsPage.js` (line 11)
- `SetupWizard.js` (lines 92, 125, 148, 195, 205)
- `App.js` (line 26)

**Setup .env.example:**
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

---

### 2. Implement Content Sanitization
**Impact:** Prevents XSS attacks  
**Effort:** Small

Install DOMPurify for sanitizing dynamic content:

```bash
npm install dompurify
```

```javascript
// components/SafeContent.jsx
import DOMPurify from 'dompurify';

export const SafeContent = ({ html }) => {
  const sanitized = DOMPurify.sanitize(html);
  return <span dangerouslySetInnerHTML={{ __html: sanitized }} />;
};

// For text content, ensure safe rendering:
export const SafeText = ({ content }) => {
  return <span>{String(content)}</span>;
};
```

---

### 3. Remove Credentials from LocalStorage
**Impact:** Prevents credential leakage  
**Effort:** Small

```javascript
// routerDiscovery.js - BEFORE
export function saveProgress(step, data) {
  localStorage.setItem('vigilSetupProgress', JSON.stringify(progress));
}

// routerDiscovery.js - AFTER
export function saveProgress(step, data) {
  // Only save non-sensitive data
  const safeData = {
    step,
    timestamp: Date.now(),
    // Explicitly exclude credentials
  };
  sessionStorage.setItem('vigilSetupProgress', JSON.stringify(safeData));
}
```

---

### 4. Fix Dockerfile for Production
**Impact:** Required for production deployment  
**Effort:** Medium

```dockerfile
# Multi-stage build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 🟡 P1 - High (Performance & Architecture)

### 5. Add React Query for Data Management
**Impact:** Eliminates redundant fetching, adds caching  
**Effort:** Medium

```bash
npm install @tanstack/react-query
```

```javascript
// hooks/useAlerts.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAlerts, acknowledgeAlert } from '../api';

export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const response = await getAlerts();
      return response.data;
    },
    refetchInterval: 30000,
  });
};

export const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
};
```

---

### 6. Implement Error Boundary
**Impact:** Prevents complete app crashes  
**Effort:** Small

```javascript
// components/ErrorBoundary.jsx
import { Component } from 'react';

export class ErrorBoundary extends Component {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
    // Send to error tracking service
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

---

### 7. Standardize on Axios API Client
**Impact:** Consistent error handling, interceptors  
**Effort:** Medium

Update components using raw fetch to use the api client:

```javascript
// DevicesPage.js - AFTER
import { getDevices } from '../api';

const fetchDevices = async () => {
  const response = await getDevices();
  setDevices(response.data.devices || []);
};

// Add to api.js
export const getDevices = () => api.get('/api/devices');
export const getAgents = () => api.get('/api/agents');
```

---

### 8. Add Axios Interceptors
**Impact:** Centralized auth, error handling  
**Effort:** Small

```javascript
// api.js - Add interceptors
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error);
  }
);
```

---

## 🟢 P2 - Medium (Code Quality & DX)

### 9. Migrate to TypeScript
**Impact:** Type safety, better IDE support  
**Effort:** Large (incremental migration possible)

```bash
npm install --save-dev typescript @types/react @types/react-dom
npx tsc --init
```

Start with API types:

```typescript
// types/api.ts
export interface Alert {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  acknowledged: boolean;
  timestamp: string;
}

export interface Device {
  id: string;
  nickname?: string;
  hostname?: string;
  ip?: string;
  mac?: string;
  online: boolean;
}
```

---

### 10. Refactor SetupWizard Component
**Impact:** Better maintainability, testability  
**Effort:** Large

**New structure:**
```
src/components/setup/
├── SetupWizard/           # Container
│   ├── index.tsx
│   ├── useWizard.ts       # Hook for wizard state
│   └── StepIndicator.tsx
├── steps/
│   ├── WelcomeStep.tsx
│   ├── RouterDiscoveryStep.tsx
│   ├── CredentialsStep.tsx
│   ├── DeviceScanStep.tsx
│   └── ConfirmationStep.tsx
```

---

### 11. Add CSS Modules or Tailwind
**Impact:** Scoped styles, design system  
**Effort:** Medium

**Tailwind approach (recommended):**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
```

```css
/* index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .widget {
    @apply bg-slate-800 rounded-lg p-5 border border-slate-700;
  }
}
```

---

### 12. Implement React Router Layout Pattern
**Impact:** Cleaner routing, less duplication  
**Effort:** Small

```javascript
// App.js - AFTER
import { Outlet } from 'react-router-dom';

const Layout = () => {
  const location = useLocation();
  const title = getPageTitle(location.pathname);
  
  return (
    <div className="app">
      <header>...</header>
      <main><Outlet /></main>
      <footer>...</footer>
    </div>
  );
};

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/devices', element: <DevicesPage /> },
      ...
    ]
  }
]);
```

---

### 13. Add Testing Framework
**Impact:** Prevents regressions  
**Effort:** Medium

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event msw
```

```javascript
// AlertPanel.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AlertPanel } from './AlertPanel';

const queryClient = new QueryClient();

test('renders alerts', async () => {
  render(
    <QueryClientProvider client={queryClient}>
      <AlertPanel />
    </QueryClientProvider>
  );
  
  await waitFor(() => {
    expect(screen.getByText('Alerts')).toBeInTheDocument();
  });
});
```

---

### 14. Add ESLint & Prettier Configuration
**Impact:** Consistent code style  
**Effort:** Small

```json
// .eslintrc.json
{
  "extends": [
    "react-app",
    "react-app/jest",
    "plugin:security/recommended",
    "plugin:jsx-a11y/recommended"
  ],
  "plugins": ["security", "jsx-a11y"]
}
```

---

## 🔵 P3 - Low (Nice to Have)

### 15. Add WebSocket Support
**Impact:** Real-time updates without polling  
**Effort:** Medium

```javascript
// hooks/useWebSocket.js
import { useEffect, useRef } from 'react';

export const useWebSocket = (url, onMessage) => {
  const ws = useRef(null);
  
  useEffect(() => {
    ws.current = new WebSocket(url);
    ws.current.onmessage = (event) => {
      onMessage(JSON.parse(event.data));
    };
    return () => ws.current?.close();
  }, [url]);
};
```

---

### 16. Add React Lazy Loading
**Impact:** Smaller initial bundle  
**Effort:** Small

```javascript
// App.js
const DevicesPage = React.lazy(() => import('./pages/DevicesPage'));
const AlertsPage = React.lazy(() => import('./pages/AlertsPage'));

// Wrap in Suspense
<Suspense fallback={<Loading />}>
  <Routes>...</Routes>
</Suspense>
```

---

### 17. Add Bundle Analysis
**Impact:** Monitor bundle size  
**Effort:** Small

```bash
npm install --save-dev webpack-bundle-analyzer
```

```json
// package.json
"scripts": {
  "analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"
}
```

---

### 18. Implement useMemo/useCallback Optimizations
**Impact:** Reduce unnecessary re-renders  
**Effort:** Medium

```javascript
// AccessHeatmap.js - AFTER
const filteredData = useMemo(
  () => accessData.filter(item => item.count > 0),
  [accessData]
);

// EventTimeline.js - AFTER
const formatTime = useCallback((timestamp) => {
  return new Date(timestamp).toLocaleTimeString(...);
}, []);
```

---

## Summary: Recommended Implementation Order

### Week 1 (Security & Stability)
1. ✅ Environment-based API URLs (P0)
2. ✅ Content sanitization (P0)
3. ✅ Remove credentials from localStorage (P0)
4. ✅ Error boundary implementation (P1)
5. ✅ Axios interceptors (P1)

### Week 2 (Performance & Architecture)
6. ✅ React Query integration (P1)
7. ✅ Standardize on Axios (P1)
8. ✅ useMemo/useCallback optimizations (P3)

### Week 3 (Developer Experience)
9. ✅ ESLint/Prettier setup (P2)
10. ✅ Layout refactor (P2)
11. ✅ Testing framework (P2)

### Month 2 (Major Refactors)
12. ✅ TypeScript migration (P2)
13. ✅ SetupWizard component split (P2)
14. ✅ CSS → Tailwind migration (P2)
15. ✅ Docker production build (P0)

---

*Last Updated: 2026-05-26*

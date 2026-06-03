/**
 * Custom Hook Tests
 * useAlerts Hook Tests
 * 
 * Tests for alert data fetching and management hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAlerts, useAcknowledgeAlert, useAcknowledgeAllAlerts } from '@/hooks/useAlerts';
import { server } from '@mocks/server';
import { http, HttpResponse } from 'msw';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useAlerts', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('should fetch alerts on mount', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAlerts(), { wrapper });
    
    expect(result.current.isLoading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.alerts).toBeDefined();
  });

  it('should filter alerts by severity', async () => {
    server.use(
      http.get('*/api/alerts', ({ request }) => {
        const url = new URL(request.url);
        const severity = url.searchParams.get('severity');
        
        return HttpResponse.json({
          alerts: severity === 'critical' 
            ? [{ id: 'alert-1', severity: 'critical' }]
            : [{ id: 'alert-1', severity: 'critical' }, { id: 'alert-2', severity: 'high' }],
          new_count: severity === 'critical' ? 1 : 2,
          acknowledged_count: 0,
        });
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAlerts({ severity: 'critical' }), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.alerts.every(a => a.severity === 'critical')).toBe(true);
  });

  it('should filter alerts by status', async () => {
    server.use(
      http.get('*/api/alerts', ({ request }) => {
        const url = new URL(request.url);
        const status = url.searchParams.get('status');
        
        return HttpResponse.json({
          alerts: status === 'unacknowledged'
            ? [{ id: 'alert-1', acknowledged: false }]
            : [{ id: 'alert-1', acknowledged: false }, { id: 'alert-2', acknowledged: true }],
          new_count: 1,
          acknowledged_count: status === 'unacknowledged' ? 0 : 1,
        });
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAlerts({ status: 'unacknowledged' }), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.alerts.every(a => !a.acknowledged)).toBe(true);
  });
});

describe('useAcknowledgeAlert', () => {
  it('should call acknowledge API when executed', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAcknowledgeAlert(), { wrapper });
    
    result.current.mutate('alert-123');
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('should handle acknowledge errors', async () => {
    server.use(
      http.post('*/api/alerts/:id/acknowledge', () => {
        return HttpResponse.json(
          { detail: 'Alert not found' },
          { status: 404 }
        );
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAcknowledgeAlert(), { wrapper });
    
    result.current.mutate('invalid-id');
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useAcknowledgeAllAlerts', () => {
  it('should acknowledge all alerts when executed', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAcknowledgeAllAlerts(), { wrapper });
    
    result.current.mutate();
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.count).toBeDefined();
  });
});

/**
 * Custom Hook Tests
 * useDevices Hook Tests
 * 
 * Tests for device data fetching and management hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDevices } from '@/hooks/useDevices';
import { server } from '@mocks/server';
import { http, HttpResponse } from 'msw';

// Create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useDevices', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('should fetch devices on mount', async () => {
    const wrapper = createWrapper();
    
    const { result } = renderHook(() => useDevices(), { wrapper });
    
    expect(result.current.isLoading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.devices).toBeDefined();
    expect(result.current.data?.devices.length).toBeGreaterThan(0);
  });

  it('should support filtering by containment status', async () => {
    server.use(
      http.get('*/api/devices', ({ request }) => {
        const url = new URL(request.url);
        const status = url.searchParams.get('containment_status');
        
        return HttpResponse.json({
          count: status === 'contained' ? 1 : 9,
          devices: status === 'contained' 
            ? [{ id: 'device-contained', containment_status: 'contained' }]
            : Array.from({ length: 9 }, (_, i) => ({ id: `device-${i}` })),
        });
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDevices({ containment_status: 'contained' }), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.devices.length).toBe(1);
  });

  it('should support pagination', async () => {
    server.use(
      http.get('*/api/devices', ({ request }) => {
        const url = new URL(request.url);
        const limit = parseInt(url.searchParams.get('limit') || '50', 10);
        
        return HttpResponse.json({
          count: 25,
          devices: Array.from({ length: limit }, (_, i) => ({ id: `device-${i}` })),
        });
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDevices({ limit: 10 }), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.devices.length).toBe(10);
  });

  it('should handle errors gracefully', async () => {
    server.use(
      http.get('*/api/devices', () => {
        return HttpResponse.json(
          { detail: 'Database connection failed' },
          { status: 500 }
        );
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDevices(), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    
    expect(result.current.error?.message).toContain('Database connection failed');
  });

  it('should refetch on demand', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDevices(), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    // Trigger refetch
    result.current.refetch();
    
    await waitFor(() => {
      expect(result.current.isFetching).toBe(true);
    });
  });
});

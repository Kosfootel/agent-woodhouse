/**
 * Custom Hook Tests
 * useSetup Hook Tests
 * 
 * Tests for setup wizard state management hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSetup, useRouterDiscovery, useValidateCredentials, useScanDevices } from '@/hooks/useSetup';
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

describe('useSetup', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('should check setup status on mount', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSetup(), { wrapper });
    
    expect(result.current.isLoading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.is_setup_complete).toBeDefined();
  });

  it('should create setup session', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSetup(), { wrapper });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.session_id).toBeDefined();
  });
});

describe('useRouterDiscovery', () => {
  it('should discover routers when executed', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useRouterDiscovery(), { wrapper });
    
    act(() => {
      result.current.mutate();
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.routers).toBeDefined();
    expect(result.current.data?.routers.length).toBeGreaterThan(0);
  });

  it('should handle discovery errors', async () => {
    server.use(
      http.post('*/api/setup/discover', () => {
        return HttpResponse.json(
          { detail: 'Discovery failed' },
          { status: 500 }
        );
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useRouterDiscovery(), { wrapper });
    
    act(() => {
      result.current.mutate();
    });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useValidateCredentials', () => {
  it('should validate credentials successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useValidateCredentials(), { wrapper });
    
    const credentials = {
      router_ip: '192.168.50.1',
      admin_username: 'admin',
      admin_password: 'password123',
    };
    
    act(() => {
      result.current.mutate(credentials);
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.router).toBeDefined();
  });

  it('should fail with invalid credentials', async () => {
    server.use(
      http.post('*/api/setup/router-credentials', () => {
        return HttpResponse.json(
          { detail: 'Authentication failed' },
          { status: 401 }
        );
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useValidateCredentials(), { wrapper });
    
    const credentials = {
      router_ip: '192.168.50.1',
      admin_username: 'admin',
      admin_password: 'wrong-password',
    };
    
    act(() => {
      result.current.mutate(credentials);
    });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useScanDevices', () => {
  it('should scan for devices when executed', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useScanDevices(), { wrapper });
    
    act(() => {
      result.current.mutate({ ip: '192.168.50.1' });
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.success).toBe(true);
  });

  it('should handle scan errors', async () => {
    server.use(
      http.post('*/api/setup/connect', () => {
        return HttpResponse.json(
          { success: false, message: 'Scan failed' },
          { status: 500 }
        );
      })
    );
    
    const wrapper = createWrapper();
    const { result } = renderHook(() => useScanDevices(), { wrapper });
    
    act(() => {
      result.current.mutate({ ip: '192.168.50.1' });
    });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

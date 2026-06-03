/**
 * Integration Tests
 * Dashboard Page Integration Tests
 * 
 * Tests for the main dashboard page combining multiple components
 * and user workflows.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import App from '@/App';
import { server } from '@mocks/server';
import { http, HttpResponse } from 'msw';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const createWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
};

describe('Dashboard Page Integration', () => {
  beforeEach(() => {
    server.resetHandlers();
    vi.stubEnv('REACT_APP_API_URL', 'http://localhost:8000');
  });

  it('should redirect to setup if setup not complete', async () => {
    server.use(
      http.get('*/api/setup/status', () => {
        return HttpResponse.json({ is_setup_complete: false });
      })
    );
    
    render(<App />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText("Let's set up your Vigil device")).toBeInTheDocument();
    });
  });

  it('should render dashboard when setup is complete', async () => {
    server.use(
      http.get('*/api/setup/status', () => {
        return HttpResponse.json({ is_setup_complete: true });
      })
    );
    
    render(<App />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Vigil Dashboard')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Security Event Timeline')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
  });

  it('should load dashboard widgets with data', async () => {
    server.use(
      http.get('*/api/setup/status', () => {
        return HttpResponse.json({ is_setup_complete: true });
      }),
      http.get('*/api/security/events', () => {
        return HttpResponse.json({
          events: [
            { id: 'event-1', event_type: 'security_event', severity: 'critical', agent: 'agent-1', details: 'Test', timestamp: new Date().toISOString() },
          ],
        });
      }),
      http.get('*/api/alerts', () => {
        return HttpResponse.json({
          alerts: [{ id: 'alert-1', title: 'Test Alert', severity: 'high', acknowledged: false }],
          new_count: 1,
          acknowledged_count: 0,
        });
      }),
      http.get('*/api/security/blocked-stats', () => {
        return HttpResponse.json({ total_blocked: 42, today_blocked: 5 });
      })
    );
    
    render(<App />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Security Event Timeline')).toBeInTheDocument();
    });
    
    // Widgets should load with data
    await waitFor(() => {
      expect(screen.getByText('Test Alert')).toBeInTheDocument();
    });
  });

  it('should navigate between pages using navigation', async () => {
    const user = userEvent.setup();
    
    server.use(
      http.get('*/api/setup/status', () => {
        return HttpResponse.json({ is_setup_complete: true });
      }),
      http.get('*/api/devices', () => {
        return HttpResponse.json({ devices: [], count: 0 });
      })
    );
    
    render(<App />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Vigil Dashboard')).toBeInTheDocument();
    });
    
    // Navigate to devices
    const devicesLink = screen.getByText('Devices');
    await user.click(devicesLink);
    
    await waitFor(() => {
      expect(screen.getByText('Device Management')).toBeInTheDocument();
    });
  });

  it('should display error state when API fails', async () => {
    server.use(
      http.get('*/api/setup/status', () => {
        return HttpResponse.json({ is_setup_complete: true });
      }),
      http.get('*/api/security/events', () => {
        return HttpResponse.error();
      })
    );
    
    render(<App />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Vigil Dashboard')).toBeInTheDocument();
    });
    
    // Widgets should still render even with errors
    await waitFor(() => {
      expect(screen.getByText('Security Event Timeline')).toBeInTheDocument();
    });
  });

  it('should show loading state while checking setup status', async () => {
    server.use(
      http.get('*/api/setup/status', async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return HttpResponse.json({ is_setup_complete: true });
      })
    );
    
    render(<App />, { wrapper: createWrapper });
    
    // Should show loading initially
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Vigil Dashboard')).toBeInTheDocument();
    });
  });
});

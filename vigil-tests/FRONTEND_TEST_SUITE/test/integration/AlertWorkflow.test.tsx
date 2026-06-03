/**
 * Integration Tests
 * Alert Workflow Integration Tests
 * 
 * End-to-end workflow tests for alert management.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AlertsPage from '@/pages/AlertsPage';
import { server } from '@mocks/server';
import { http, HttpResponse } from 'msw';

const createWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
};

describe('Alert Workflow Integration', () => {
  const mockAlerts = [
    { id: 'alert-1', title: 'Critical Alert', description: 'Security breach', severity: 'critical', source: 'Agent-1', timestamp: new Date().toISOString(), acknowledged: false },
    { id: 'alert-2', title: 'High Alert', description: 'Policy violation', severity: 'high', source: 'System', timestamp: new Date(Date.now() - 3600000).toISOString(), acknowledged: false },
    { id: 'alert-3', title: 'Info Alert', description: 'System update', severity: 'info', source: 'System', timestamp: new Date(Date.now() - 7200000).toISOString(), acknowledged: true },
  ];

  beforeEach(() => {
    server.resetHandlers();
    vi.stubGlobal('confirm', vi.fn(() => true));
  });

  it('should display unacknowledged alerts prominently', async () => {
    server.use(
      http.get('*/api/alerts', () => HttpResponse.json({ alerts: mockAlerts, new_count: 2, acknowledged_count: 1 }))
    );
    
    render(<AlertsPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Critical Alert')).toBeInTheDocument();
      expect(screen.getByText('High Alert')).toBeInTheDocument();
    });
    
    expect(screen.getByText('2 New')).toBeInTheDocument();
  });

  it('should acknowledge single alert', async () => {
    const user = userEvent.setup();
    
    server.use(
      http.get('*/api/alerts', () => HttpResponse.json({ alerts: [mockAlerts[0]], new_count: 1, acknowledged_count: 0 })),
      http.post('*/api/alerts/:id/acknowledge', () => HttpResponse.json({ acknowledged: true }))
    );
    
    render(<AlertsPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Critical Alert')).toBeInTheDocument();
    });
    
    const ackBtn = screen.getByRole('button', { name: /acknowledge/i });
    await user.click(ackBtn);
    
    await waitFor(() => {
      expect(screen.queryByText('1 New')).not.toBeInTheDocument();
    });
  });

  it('should acknowledge all alerts in bulk', async () => {
    const user = userEvent.setup();
    
    server.use(
      http.get('*/api/alerts', () => HttpResponse.json({ alerts: mockAlerts.slice(0, 2), new_count: 2, acknowledged_count: 0 })),
      http.post('*/api/alerts/acknowledge-all', () => HttpResponse.json({ acknowledged: true, count: 2 }))
    );
    
    render(<AlertsPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Critical Alert')).toBeInTheDocument();
    });
    
    const ackAllBtn = screen.getByRole('button', { name: /acknowledge all/i });
    await user.click(ackAllBtn);
    
    expect(window.confirm).toHaveBeenCalledWith('Acknowledge all 2 unacknowledged alerts?');
  });

  it('should filter alerts by severity level', async () => {
    const user = userEvent.setup();
    
    server.use(
      http.get('*/api/alerts', ({ request }) => {
        const url = new URL(request.url);
        const severity = url.searchParams.get('severity');
        const filtered = severity ? mockAlerts.filter(a => a.severity === severity) : mockAlerts;
        return HttpResponse.json({ alerts: filtered, new_count: filtered.filter(a => !a.acknowledged).length, acknowledged_count: filtered.filter(a => a.acknowledged).length });
      })
    );
    
    render(<AlertsPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
    
    await user.selectOptions(screen.getByRole('combobox'), 'critical');
    
    await waitFor(() => {
      expect(screen.getByText('Critical Alert')).toBeInTheDocument();
      expect(screen.queryByText('High Alert')).not.toBeInTheDocument();
    });
  });

  it('should show alert detail view', async () => {
    // Test clicking on alert to view details
  });

  it('should display alert statistics', async () => {
    // Test statistics display
  });

  it('should handle real-time alert updates', async () => {
    // Test SSE/WebSocket updates
  });
});

/**
 * Component Unit Tests
 * AlertsPage Component Tests
 * 
 * Tests for the full alerts management page covering
 * filtering, bulk actions, and detailed alert views.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AlertsPage from '@/pages/AlertsPage';

// Mock window.confirm
Object.defineProperty(window, 'confirm', {
  writable: true,
  value: vi.fn(),
});

// Mock fetch
global.fetch = vi.fn();

describe('AlertsPage', () => {
  const mockAlerts = [
    {
      id: 'alert-1',
      title: 'Critical Security Breach',
      description: 'Unauthorized access detected',
      severity: 'critical',
      source: 'Agent-1',
      timestamp: new Date().toISOString(),
      acknowledged: false,
    },
    {
      id: 'alert-2',
      title: 'High Priority Alert',
      description: 'Policy violation detected',
      severity: 'high',
      source: 'System',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      acknowledged: false,
    },
    {
      id: 'alert-3',
      title: 'Info Alert',
      description: 'System update completed',
      severity: 'info',
      source: 'System',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      acknowledged: true,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(window.confirm).mockReturnValue(true);
  });

  it('should render loading state initially', () => {
    vi.mocked(global.fetch).mockImplementation(() => new Promise(() => {}));
    
    render(<AlertsPage />);
    
    expect(screen.getByText('Loading alerts...')).toBeInTheDocument();
  });

  it('should display alerts after loading', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Critical Security Breach')).toBeInTheDocument();
    });
    
    expect(screen.getByText('High Priority Alert')).toBeInTheDocument();
  });

  it('should show new alerts count badge', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('2 New')).toBeInTheDocument();
    });
  });

  it('should display filter dropdown', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  it('should filter alerts by severity', async () => {
    const user = userEvent.setup();
    
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
    
    await user.selectOptions(screen.getByRole('combobox'), 'critical');
    
    // Filter would be applied - component updates filteredAlerts
    await waitFor(() => {
      expect(screen.getByText('Critical Only')).toBeInTheDocument();
    });
  });

  it('should show acknowledge all button when unacknowledged alerts exist', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /acknowledge all/i })).toBeInTheDocument();
    });
  });

  it('should call acknowledge all API when confirming', async () => {
    const user = userEvent.setup();
    
    vi.mocked(global.fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ alerts: mockAlerts, new_count: 2 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ count: 2 }),
      } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /acknowledge all/i })).toBeInTheDocument();
    });
    
    const ackAllBtn = screen.getByRole('button', { name: /acknowledge all/i });
    await user.click(ackAllBtn);
    
    expect(window.confirm).toHaveBeenCalledWith('Acknowledge all 2 unacknowledged alerts?');
  });

  it('should not acknowledge if user cancels confirmation', async () => {
    const user = userEvent.setup();
    vi.mocked(window.confirm).mockReturnValue(false);
    
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /acknowledge all/i })).toBeInTheDocument();
    });
    
    const ackAllBtn = screen.getByRole('button', { name: /acknowledge all/i });
    await user.click(ackAllBtn);
    
    // Should not have made second API call
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('should acknowledge single alert', async () => {
    const user = userEvent.setup();
    
    vi.mocked(global.fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ alerts: [mockAlerts[0]], new_count: 1 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ acknowledged: true }),
      } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Critical Security Breach')).toBeInTheDocument();
    });
    
    const ackBtn = screen.getByRole('button', { name: /acknowledge/i });
    await user.click(ackBtn);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts/alert-1/acknowledge'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  it('should display empty state when no alerts match filter', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [], new_count: 0 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('✅ No alerts to display')).toBeInTheDocument();
    });
    
    expect(screen.getByText('System is secure')).toBeInTheDocument();
  });

  it('should show severity badges', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [mockAlerts[0]], new_count: 1 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    });
  });

  it('should format timestamps', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ 
        alerts: [{
          ...mockAlerts[0],
          timestamp: '2024-01-15T14:30:00.000Z',
        }], 
        new_count: 1 
      }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      // Should show formatted date
      expect(screen.getByText(/Jan|15|2024/)).toBeInTheDocument();
    });
  });

  it('should poll for alert updates', async () => {
    vi.useFakeTimers();
    
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ alerts: mockAlerts, new_count: 2 }),
    } as Response);
    
    render(<AlertsPage />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
    
    // Advance timer past polling interval (10 seconds)
    vi.advanceTimersByTime(11000);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
    
    vi.useRealTimers();
  });
});

/**
 * Component Unit Tests
 * AlertPanel Component Tests
 * 
 * Tests for the security alert management component
 * covering loading states, data display, and user interactions.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AlertPanel from '@/components/AlertPanel';
import { server } from '@mocks/server';
import { http, HttpResponse } from 'msw';

// Mock the API module
vi.mock('@/api', () => ({
  getAlerts: vi.fn(),
  acknowledgeAlert: vi.fn(),
  acknowledgeAllAlerts: vi.fn(),
}));

import { getAlerts, acknowledgeAlert, acknowledgeAllAlerts } from '@/api';

describe('AlertPanel', () => {
  const mockAlerts = [
    {
      id: 'alert-1',
      title: 'Unauthorized Access Detected',
      alert_type: 'unauthorized_access',
      severity: 'critical',
      narrative: 'Suspicious login attempt detected',
      device_id: 'device-1',
      timestamp: new Date().toISOString(),
      acknowledged: false,
    },
    {
      id: 'alert-2',
      title: 'Policy Violation',
      alert_type: 'policy_violation',
      severity: 'high',
      narrative: 'Device exceeded data threshold',
      device_id: 'device-2',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      acknowledged: true,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    vi.mocked(getAlerts).mockImplementation(() => new Promise(() => {}));
    
    render(<AlertPanel />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should display alerts after loading', async () => {
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: mockAlerts,
        new_count: 1,
        acknowledged_count: 1,
      },
    });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Unauthorized Access Detected')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Policy Violation')).toBeInTheDocument();
    expect(screen.getByText('1 new')).toBeInTheDocument();
  });

  it('should display empty state when no alerts', async () => {
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: [],
        new_count: 0,
        acknowledged_count: 0,
      },
    });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('🎉 No active alerts')).toBeInTheDocument();
    });
    
    expect(screen.getByText('System is operating normally')).toBeInTheDocument();
  });

  it('should call acknowledge API when clicking acknowledge button', async () => {
    const user = userEvent.setup();
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: [mockAlerts[0]],
        new_count: 1,
        acknowledged_count: 0,
      },
    });
    vi.mocked(acknowledgeAlert).mockResolvedValue({ data: {} });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Unauthorized Access Detected')).toBeInTheDocument();
    });
    
    const ackButton = screen.getByRole('button', { name: /ack/i });
    await user.click(ackButton);
    
    expect(acknowledgeAlert).toHaveBeenCalledWith('alert-1');
  });

  it('should show acknowledge all button when unacknowledged alerts exist', async () => {
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: mockAlerts,
        new_count: 1,
        acknowledged_count: 1,
      },
    });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /acknowledge all/i })).toBeInTheDocument();
    });
  });

  it('should call acknowledge all API when clicking acknowledge all', async () => {
    const user = userEvent.setup();
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: [mockAlerts[0]],
        new_count: 1,
        acknowledged_count: 0,
      },
    });
    vi.mocked(acknowledgeAllAlerts).mockResolvedValue({ data: {} });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /acknowledge all/i })).toBeInTheDocument();
    });
    
    const ackAllButton = screen.getByRole('button', { name: /acknowledge all/i });
    await user.click(ackAllButton);
    
    expect(acknowledgeAllAlerts).toHaveBeenCalled();
  });

  it('should display error state when API fails', async () => {
    vi.mocked(getAlerts).mockRejectedValue(new Error('Network error'));
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should render severity badges with correct colors', async () => {
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: mockAlerts,
        new_count: 1,
        acknowledged_count: 1,
      },
    });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      const criticalBadge = screen.getByText('CRITICAL');
      expect(criticalBadge).toHaveStyle({
        backgroundColor: '#dc2626',
        color: 'white',
      });
    });
  });

  it('should format timestamps correctly', async () => {
    const alertWithTimestamp = {
      ...mockAlerts[0],
      timestamp: '2024-01-15T14:30:00.000Z',
    };
    
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: [alertWithTimestamp],
        new_count: 1,
        acknowledged_count: 0,
      },
    });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      // Should display formatted time
      expect(screen.getByText(/Jan 15/)).toBeInTheDocument();
    });
  });

  it('should show alert device ID', async () => {
    vi.mocked(getAlerts).mockResolvedValue({
      data: {
        alerts: [mockAlerts[0]],
        new_count: 1,
        acknowledged_count: 0,
      },
    });
    
    render(<AlertPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Device #device-1')).toBeInTheDocument();
    });
  });
});

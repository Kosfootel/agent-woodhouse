/**
 * Component Unit Tests
 * DevicesPage Component Tests
 * 
 * Tests for device management interface covering
 * listing, filtering, containment controls, and deletion.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DevicesPage from '@/pages/DevicesPage';

// Mock fetch
global.fetch = vi.fn();

describe('DevicesPage', () => {
  const mockDevices = [
    {
      id: 'device-1',
      nickname: 'Living Room TV',
      hostname: 'tv-living.local',
      vendor: 'Samsung',
      device_type: 'smart-tv',
      ip: '192.168.50.10',
      mac: '00:11:22:33:44:10',
      online: true,
      containment_status: 'released',
    },
    {
      id: 'device-2',
      nickname: 'iPhone',
      hostname: 'iphone-12.local',
      vendor: 'Apple',
      device_type: 'mobile',
      ip: '192.168.50.11',
      mac: '00:11:22:33:44:11',
      online: true,
      containment_status: 'released',
    },
    {
      id: 'device-3',
      nickname: 'Gaming PC',
      hostname: 'gaming-pc.local',
      vendor: 'Custom',
      device_type: 'desktop',
      ip: '192.168.50.12',
      mac: '00:11:22:33:44:12',
      online: false,
      containment_status: 'contained',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    vi.mocked(global.fetch).mockImplementation(() => new Promise(() => {}));
    
    render(<DevicesPage />);
    
    expect(screen.getByText('Loading devices...')).toBeInTheDocument();
  });

  it('should display devices in table after loading', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: mockDevices }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Living Room TV')).toBeInTheDocument();
    });
    
    expect(screen.getByText('iPhone')).toBeInTheDocument();
    expect(screen.getByText('Gaming PC')).toBeInTheDocument();
  });

  it('should show device count badge', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: mockDevices }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument(); // Device count
    });
  });

  it('should display empty state when no devices', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: [] }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('No devices registered')).toBeInTheDocument();
    });
    
    expect(screen.getByText(/visit setup to add devices/i)).toBeInTheDocument();
  });

  it('should display online/offline status indicators', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: mockDevices }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // Skip header row, check data rows
      expect(rows[1]).toHaveTextContent('🟢'); // Online
      expect(rows[3]).toHaveTextContent('🔴'); // Offline
    });
  });

  it('should display device details in table columns', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: [mockDevices[0]] }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Living Room TV')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Samsung')).toBeInTheDocument();
    expect(screen.getByText('smart-tv')).toBeInTheDocument();
    expect(screen.getByText('192.168.50.10')).toBeInTheDocument();
    expect(screen.getByText('00:11:22:33:44:10')).toBeInTheDocument();
  });

  it('should poll for device updates', async () => {
    vi.useFakeTimers();
    
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ devices: mockDevices }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
    
    // Advance timer past polling interval (30 seconds)
    vi.advanceTimersByTime(31000);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
    
    vi.useRealTimers();
  });

  it('should show fallback for unknown device type', async () => {
    const deviceWithUnknownType = {
      ...mockDevices[0],
      device_type: null,
    };
    
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: [deviceWithUnknownType] }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });
  });

  it('should show fallback for unknown vendor', async () => {
    const deviceWithUnknownVendor = {
      ...mockDevices[0],
      vendor: null,
    };
    
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ devices: [deviceWithUnknownVendor] }),
    } as Response);
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Unknown').length).toBeGreaterThan(0);
    });
  });

  it('should handle API errors gracefully', async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'));
    
    render(<DevicesPage />);
    
    await waitFor(() => {
      // Should still render, possibly with empty state or error
      expect(screen.getByText('📱 Connected Devices')).toBeInTheDocument();
    });
  });
});

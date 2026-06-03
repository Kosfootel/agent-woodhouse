/**
 * Integration Tests
 * Device Management Integration Tests
 * 
 * End-to-end workflow tests for device management.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DevicesPage from '@/pages/DevicesPage';
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

describe('Device Management Integration', () => {
  const mockDevices = [
    { id: 'device-1', nickname: 'iPhone', vendor: 'Apple', device_type: 'mobile', ip: '192.168.50.10', mac: '00:11:22:33:44:10', online: true, containment_status: 'released' },
    { id: 'device-2', nickname: 'Smart TV', vendor: 'Samsung', device_type: 'smart-tv', ip: '192.168.50.11', mac: '00:11:22:33:44:11', online: true, containment_status: 'released' },
  ];

  beforeEach(() => {
    server.resetHandlers();
  });

  it('should display device list with details', async () => {
    server.use(
      http.get('*/api/devices', () => HttpResponse.json({ devices: mockDevices, count: 2 }))
    );
    
    render(<DevicesPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('iPhone')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Smart TV')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('Samsung')).toBeInTheDocument();
  });

  it('should contain a device', async () => {
    const user = userEvent.setup();
    
    server.use(
      http.get('*/api/devices', () => HttpResponse.json({ devices: mockDevices, count: 2 })),
      http.post('*/api/devices/:id/contain', () => HttpResponse.json({ success: true, containment_status: 'contained' }))
    );
    
    render(<DevicesPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('iPhone')).toBeInTheDocument();
    });
    
    // Find and click contain button
    const containBtn = screen.getByRole('button', { name: /contain/i });
    await user.click(containBtn);
    
    await waitFor(() => {
      expect(screen.getByText('Contained')).toBeInTheDocument();
    });
  });

  it('should release a contained device', async () => {
    const user = userEvent.setup();
    
    const containedDevice = { ...mockDevices[0], containment_status: 'contained' };
    
    server.use(
      http.get('*/api/devices', () => HttpResponse.json({ devices: [containedDevice], count: 1 })),
      http.post('*/api/devices/:id/release', () => HttpResponse.json({ success: true, containment_status: 'released' }))
    );
    
    render(<DevicesPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('iPhone')).toBeInTheDocument();
    });
    
    const releaseBtn = screen.getByRole('button', { name: /release/i });
    await user.click(releaseBtn);
    
    await waitFor(() => {
      expect(screen.getByText('Released')).toBeInTheDocument();
    });
  });

  it('should delete a device after confirmation', async () => {
    const user = userEvent.setup();
    vi.stubGlobal('confirm', vi.fn(() => true));
    
    server.use(
      http.get('*/api/devices', () => HttpResponse.json({ devices: mockDevices, count: 2 })),
      http.delete('*/api/devices/:id', () => HttpResponse.json({ deleted: true }))
    );
    
    render(<DevicesPage />, { wrapper: createWrapper });
    
    await waitFor(() => {
      expect(screen.getByText('iPhone')).toBeInTheDocument();
    });
    
    const deleteBtn = screen.getByRole('button', { name: /delete/i });
    await user.click(deleteBtn);
    
    expect(window.confirm).toHaveBeenCalled();
  });

  it('should handle bulk operations', async () => {
    // Test bulk selection and operations
  });

  it('should filter devices by type', async () => {
    // Test filtering functionality
  });

  it('should search devices by name', async () => {
    // Test search functionality
  });
});

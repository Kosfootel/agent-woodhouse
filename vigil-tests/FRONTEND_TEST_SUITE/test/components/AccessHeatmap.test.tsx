/**
 * Component Unit Tests
 * AccessHeatmap Component Tests
 * 
 * Tests for memory access visualization component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import AccessHeatmap from '@/components/AccessHeatmap';
import { getMemoryAccess } from '@/api';

vi.mock('@/api', () => ({
  getMemoryAccess: vi.fn(),
}));

describe('AccessHeatmap', () => {
  const mockAccessData = [
    { agent: 'agent-1', level: 'critical', count: 15 },
    { agent: 'agent-2', level: 'high', count: 23 },
    { agent: 'agent-3', level: 'medium', count: 8 },
    { agent: 'agent-1', level: 'low', count: 45 },
    { agent: 'agent-2', level: 'low', count: 12 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    vi.mocked(getMemoryAccess).mockImplementation(() => new Promise(() => {}));
    
    render(<AccessHeatmap />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should display access data after loading', async () => {
    vi.mocked(getMemoryAccess).mockResolvedValue({
      data: { data: mockAccessData },
    });
    
    render(<AccessHeatmap />);
    
    await waitFor(() => {
      expect(screen.getByText('agent-1')).toBeInTheDocument();
    });
    
    expect(screen.getByText('agent-2')).toBeInTheDocument();
    expect(screen.getByText('agent-3')).toBeInTheDocument();
  });

  it('should display empty state when no access data', async () => {
    vi.mocked(getMemoryAccess).mockResolvedValue({
      data: { data: [] },
    });
    
    render(<AccessHeatmap />);
    
    await waitFor(() => {
      expect(screen.getByText('No memory access recorded yet')).toBeInTheDocument();
    });
  });

  it('should filter out entries with zero count', async () => {
    vi.mocked(getMemoryAccess).mockResolvedValue({
      data: {
        data: [
          ...mockAccessData,
          { agent: 'agent-4', level: 'critical', count: 0 },
        ],
      },
    });
    
    render(<AccessHeatmap />);
    
    await waitFor(() => {
      expect(screen.getByText('agent-1')).toBeInTheDocument();
    });
    
    // agent-4 with count 0 should not appear
    expect(screen.queryByText('agent-4')).not.toBeInTheDocument();
  });

  it('should render severity levels with correct colors', async () => {
    vi.mocked(getMemoryAccess).mockResolvedValue({
      data: { data: mockAccessData },
    });
    
    render(<AccessHeatmap />);
    
    await waitFor(() => {
      const criticalCell = screen.getByText('critical');
      expect(criticalCell).toHaveStyle({ color: '#dc2626' });
    });
    
    const highCell = screen.getByText('high');
    expect(highCell).toHaveStyle({ color: '#ea580c' });
  });

  it('should display access counts in table', async () => {
    vi.mocked(getMemoryAccess).mockResolvedValue({
      data: { data: mockAccessData },
    });
    
    render(<AccessHeatmap />);
    
    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument(); // critical count
      expect(screen.getByText('23')).toBeInTheDocument(); // high count
      expect(screen.getByText('45')).toBeInTheDocument(); // low count
    });
  });

  it('should handle API errors gracefully', async () => {
    vi.mocked(getMemoryAccess).mockRejectedValue(new Error('API Error'));
    
    render(<AccessHeatmap />);
    
    await waitFor(() => {
      expect(screen.getByText(/API Error/)).toBeInTheDocument();
    });
  });
});

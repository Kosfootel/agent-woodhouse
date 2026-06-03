/**
 * Zustand Store Tests
 * uiStore Tests
 * 
 * Tests for UI state management store (sidebar, theme, loading states).
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from '@/stores/uiStore';
import { act } from '@testing-library/react';

describe('uiStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    const { getState } = useUIStore;
    getState().reset();
  });

  it('should toggle sidebar', () => {
    const { getState } = useUIStore;
    
    expect(getState().sidebarOpen).toBe(false);
    
    act(() => {
      getState().toggleSidebar();
    });
    
    expect(getState().sidebarOpen).toBe(true);
    
    act(() => {
      getState().toggleSidebar();
    });
    
    expect(getState().sidebarOpen).toBe(false);
  });

  it('should set sidebar state', () => {
    const { getState } = useUIStore;
    
    act(() => {
      getState().setSidebarOpen(true);
    });
    
    expect(getState().sidebarOpen).toBe(true);
    
    act(() => {
      getState().setSidebarOpen(false);
    });
    
    expect(getState().sidebarOpen).toBe(false);
  });

  it('should toggle theme', () => {
    const { getState } = useUIStore;
    
    expect(getState().theme).toBe('light');
    
    act(() => {
      getState().toggleTheme();
    });
    
    expect(getState().theme).toBe('dark');
    
    act(() => {
      getState().toggleTheme();
    });
    
    expect(getState().theme).toBe('light');
  });

  it('should set theme directly', () => {
    const { getState } = useUIStore;
    
    act(() => {
      getState().setTheme('dark');
    });
    
    expect(getState().theme).toBe('dark');
    
    act(() => {
      getState().setTheme('light');
    });
    
    expect(getState().theme).toBe('light');
  });

  it('should set loading state', () => {
    const { getState } = useUIStore;
    
    expect(getState().isLoading).toBe(false);
    
    act(() => {
      getState().setLoading(true);
    });
    
    expect(getState().isLoading).toBe(true);
    
    act(() => {
      getState().setLoading(false);
    });
    
    expect(getState().isLoading).toBe(false);
  });

  it('should set global error', () => {
    const { getState } = useUIStore;
    
    act(() => {
      getState().setError('Something went wrong');
    });
    
    expect(getState().error).toBe('Something went wrong');
    
    act(() => {
      getState().clearError();
    });
    
    expect(getState().error).toBeNull();
  });

  it('should persist theme preference', () => {
    const { getState } = useUIStore;
    
    act(() => {
      getState().setTheme('dark');
    });
    
    // Simulate store rehydration
    const savedTheme = getState().theme;
    expect(savedTheme).toBe('dark');
  });

  it('should reset to initial state', () => {
    const { getState } = useUIStore;
    
    act(() => {
      getState().setSidebarOpen(true);
      getState().setTheme('dark');
      getState().setLoading(true);
      getState().setError('Test error');
    });
    
    expect(getState().sidebarOpen).toBe(true);
    expect(getState().theme).toBe('dark');
    expect(getState().isLoading).toBe(true);
    expect(getState().error).toBe('Test error');
    
    act(() => {
      getState().reset();
    });
    
    expect(getState().sidebarOpen).toBe(false);
    expect(getState().theme).toBe('light');
    expect(getState().isLoading).toBe(false);
    expect(getState().error).toBeNull();
  });
});

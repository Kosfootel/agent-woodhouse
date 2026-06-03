/**
 * Zustand Store Tests
 * authStore Tests
 * 
 * Tests for authentication state management store.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '@/stores/authStore';
import { act } from '@testing-library/react';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const { getState } = useAuthStore;
    getState().logout();
  });

  it('should start with unauthenticated state', () => {
    const { getState } = useAuthStore;
    
    expect(getState().isAuthenticated).toBe(false);
    expect(getState().user).toBeNull();
  });

  it('should set user on login', () => {
    const { getState } = useAuthStore;
    const user = { id: 'user-1', name: 'Test User', email: 'test@example.com' };
    
    act(() => {
      getState().login(user);
    });
    
    expect(getState().isAuthenticated).toBe(true);
    expect(getState().user).toEqual(user);
  });

  it('should clear user on logout', () => {
    const { getState } = useAuthStore;
    const user = { id: 'user-1', name: 'Test User', email: 'test@example.com' };
    
    act(() => {
      getState().login(user);
    });
    
    expect(getState().isAuthenticated).toBe(true);
    
    act(() => {
      getState().logout();
    });
    
    expect(getState().isAuthenticated).toBe(false);
    expect(getState().user).toBeNull();
  });

  it('should update user profile', () => {
    const { getState } = useAuthStore;
    const user = { id: 'user-1', name: 'Test User', email: 'test@example.com' };
    
    act(() => {
      getState().login(user);
    });
    
    act(() => {
      getState().updateUser({ name: 'Updated Name' });
    });
    
    expect(getState().user?.name).toBe('Updated Name');
    expect(getState().user?.email).toBe('test@example.com');
  });

  it('should set loading state', () => {
    const { getState } = useAuthStore;
    
    expect(getState().isLoading).toBe(false);
    
    act(() => {
      getState().setLoading(true);
    });
    
    expect(getState().isLoading).toBe(true);
  });

  it('should set error message', () => {
    const { getState } = useAuthStore;
    
    act(() => {
      getState().setError('Invalid credentials');
    });
    
    expect(getState().error).toBe('Invalid credentials');
    
    act(() => {
      getState().clearError();
    });
    
    expect(getState().error).toBeNull();
  });

  it('should check for existing session on hydrate', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify({
      id: 'user-1',
      name: 'Test User',
      email: 'test@example.com',
    }));
    
    const { getState } = useAuthStore;
    
    act(() => {
      getState().hydrate();
    });
    
    expect(getState().isAuthenticated).toBe(true);
    expect(getState().user?.name).toBe('Test User');
  });

  it('should handle invalid stored session', () => {
    localStorageMock.getItem.mockReturnValue('invalid-json');
    
    const { getState } = useAuthStore;
    
    act(() => {
      getState().hydrate();
    });
    
    expect(getState().isAuthenticated).toBe(false);
    expect(getState().user).toBeNull();
  });
});

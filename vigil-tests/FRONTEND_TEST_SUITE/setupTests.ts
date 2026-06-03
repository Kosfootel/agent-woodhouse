/**
 * Vitest + Testing Library Configuration
 * Vigil Dashboard Frontend Test Suite
 */

import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, vi } from 'vitest';
import { server } from './mocks/server';

// ============================================================================
// MSW Setup
// ============================================================================

// Start MSW server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

// Clean up after each test
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Close MSW server after all tests
afterAll(() => {
  server.close();
});

// ============================================================================
// Global Mocks
// ============================================================================

// Mock matchMedia for responsive component tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver for lazy loading/infinite scroll
class MockIntersectionObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: MockIntersectionObserver,
});

// Mock ResizeObserver for responsive components
class MockResizeObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: MockResizeObserver,
});

// Mock localStorage for setup wizard tests
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// ============================================================================
// Environment Variables
// ============================================================================

vi.stubEnv('REACT_APP_API_URL', 'http://localhost:8000');

// ============================================================================
// Console Configurations
// ============================================================================

// Suppress expected console warnings in tests
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

beforeAll(() => {
  console.warn = (...args: any[]) => {
    // Filter out React Router v7 warnings
    if (typeof args[0] === 'string' && args[0].includes('React Router')) {
      return;
    }
    originalConsoleWarn(...args);
  };

  console.error = (...args: any[]) => {
    // Filter out known test warnings
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: An update to') ||
        args[0].includes('act(...)'))
    ) {
      return;
    }
    originalConsoleError(...args);
  };
});

afterAll(() => {
  console.warn = originalConsoleWarn;
  console.error = originalConsoleError;
});

// ============================================================================
// Test Utilities
// ============================================================================

/**
 * Waits for an element to be removed from the DOM
 */
export const waitForElementToBeRemoved = async (
  callback: () => HTMLElement | null,
  options?: { timeout?: number }
): Promise<void> => {
  const { timeout = 4500 } = options || {};
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (callback() === null) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }

  throw new Error('Element was not removed within timeout');
};

/**
 * Creates a deferred promise for async test control
 */
export const createDeferred = <T>() => {
  let resolve: (value: T) => void;
  let reject: (reason: any) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve: resolve!, reject: reject! };
};

/**
 * Zustand Store Tests
 * filterStore Tests
 * 
 * Tests for filter state management store (devices, alerts, events).
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useFilterStore } from '@/stores/filterStore';
import { act } from '@testing-library/react';

describe('filterStore', () => {
  beforeEach(() => {
    const { getState } = useFilterStore;
    getState().resetAll();
  });

  describe('device filters', () => {
    it('should set device status filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setDeviceFilter('status', 'online');
      });
      
      expect(getState().deviceFilters.status).toBe('online');
    });

    it('should set device type filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setDeviceFilter('type', 'mobile');
      });
      
      expect(getState().deviceFilters.type).toBe('mobile');
    });

    it('should set device search query', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setDeviceFilter('search', 'iPhone');
      });
      
      expect(getState().deviceFilters.search).toBe('iPhone');
    });

    it('should clear device filters', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setDeviceFilter('status', 'online');
        getState().setDeviceFilter('type', 'mobile');
      });
      
      expect(getState().deviceFilters.status).toBe('online');
      expect(getState().deviceFilters.type).toBe('mobile');
      
      act(() => {
        getState().clearDeviceFilters();
      });
      
      expect(getState().deviceFilters.status).toBeNull();
      expect(getState().deviceFilters.type).toBeNull();
    });
  });

  describe('alert filters', () => {
    it('should set alert severity filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setAlertFilter('severity', 'critical');
      });
      
      expect(getState().alertFilters.severity).toBe('critical');
    });

    it('should set alert status filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setAlertFilter('status', 'unacknowledged');
      });
      
      expect(getState().alertFilters.status).toBe('unacknowledged');
    });

    it('should set alert date range', () => {
      const { getState } = useFilterStore;
      const dateRange = { start: '2024-01-01', end: '2024-01-31' };
      
      act(() => {
        getState().setAlertFilter('dateRange', dateRange);
      });
      
      expect(getState().alertFilters.dateRange).toEqual(dateRange);
    });

    it('should clear alert filters', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setAlertFilter('severity', 'critical');
        getState().setAlertFilter('status', 'unacknowledged');
      });
      
      act(() => {
        getState().clearAlertFilters();
      });
      
      expect(getState().alertFilters.severity).toBeNull();
      expect(getState().alertFilters.status).toBeNull();
    });
  });

  describe('event filters', () => {
    it('should set event type filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setEventFilter('eventType', 'security_event');
      });
      
      expect(getState().eventFilters.eventType).toBe('security_event');
    });

    it('should set event agent filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setEventFilter('agent', 'agent-1');
      });
      
      expect(getState().eventFilters.agent).toBe('agent-1');
    });

    it('should set event severity filter', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setEventFilter('severity', 'high');
      });
      
      expect(getState().eventFilters.severity).toBe('high');
    });

    it('should clear event filters', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setEventFilter('eventType', 'security_event');
        getState().setEventFilter('severity', 'high');
      });
      
      act(() => {
        getState().clearEventFilters();
      });
      
      expect(getState().eventFilters.eventType).toBeNull();
      expect(getState().eventFilters.severity).toBeNull();
    });
  });

  describe('time range filter', () => {
    it('should set time range', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setTimeRange('24h');
      });
      
      expect(getState().timeRange).toBe('24h');
      
      act(() => {
        getState().setTimeRange('7d');
      });
      
      expect(getState().timeRange).toBe('7d');
    });
  });

  describe('reset all', () => {
    it('should reset all filters to initial state', () => {
      const { getState } = useFilterStore;
      
      act(() => {
        getState().setDeviceFilter('status', 'online');
        getState().setAlertFilter('severity', 'critical');
        getState().setEventFilter('agent', 'agent-1');
        getState().setTimeRange('24h');
      });
      
      act(() => {
        getState().resetAll();
      });
      
      expect(getState().deviceFilters).toEqual({ status: null, type: null, search: null });
      expect(getState().alertFilters).toEqual({ severity: null, status: null, dateRange: null });
      expect(getState().eventFilters).toEqual({ eventType: null, agent: null, severity: null });
      expect(getState().timeRange).toBe('24h');
    });
  });
});

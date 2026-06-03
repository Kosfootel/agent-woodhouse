/**
 * MSW (Mock Service Worker) Handlers
 * Mock API responses for Vigil Dashboard testing
 */

import { http, HttpResponse } from 'msw';

// ============================================================================
// Test Data Generators
// ============================================================================

const generateDevice = (id: number, overrides = {}) => ({
  id: `device-${id}`,
  mac: `00:11:22:33:44:${id.toString().padStart(2, '0')}`,
  ip: `192.168.50.${10 + id}`,
  hostname: `device-${id}.local`,
  name: `Device ${id}`,
  nickname: null,
  vendor: id % 2 === 0 ? 'Apple' : 'Samsung',
  device_type: ['mobile', 'laptop', 'tablet', 'smart-tv', 'iot'][id % 5],
  online: id % 3 !== 0,
  last_seen: new Date(Date.now() - (id * 1000 * 60)).toISOString(),
  containment_status: id === 5 ? 'contained' : 'released',
  ...overrides,
});

const generateAlert = (id: number, overrides = {}) => ({
  id: `alert-${id}`,
  device_id: `device-${(id % 5) + 1}`,
  title: `Security Alert ${id}`,
  description: `This is a test alert description for alert ${id}`,
  narrative: `Alert narrative for ${id}`,
  severity: ['critical', 'high', 'medium', 'low', 'info'][id % 5],
  alert_type: ['unauthorized_access', 'policy_violation', 'anomaly_detected', 'threat_detected'][id % 4],
  timestamp: new Date(Date.now() - (id * 1000 * 60 * 30)).toISOString(),
  acknowledged: id > 3,
  source: ['System', 'Agent', 'Policy'][id % 3],
  ...overrides,
});

const generateEvent = (id: number, overrides = {}) => ({
  id: `event-${id}`,
  device_id: `device-${(id % 5) + 1}`,
  event_type: ['security_event', 'policy_violation', 'anomaly_detected'][id % 3],
  severity: ['critical', 'high', 'medium', 'low'][id % 4],
  agent: `agent-${(id % 3) + 1}`,
  details: `Event details for event ${id}`,
  timestamp: new Date(Date.now() - (id * 1000 * 60)).toISOString(),
  metadata: { key: `value-${id}` },
  ...overrides,
});

const generateAgent = (id: number, overrides = {}) => ({
  id: `agent-${id}`,
  hostname: `agent-host-${id}`,
  version: '1.2.3',
  capabilities: ['monitoring', 'scanning', 'containment'],
  location: `Location ${id}`,
  status: ['ONLINE', 'OFFLINE', 'ERROR', 'UPDATING'][id % 4],
  last_heartbeat: new Date(Date.now() - (id * 1000 * 60)).toISOString(),
  ...overrides,
});

// ============================================================================
// API Handlers
// ============================================================================

export const handlers = [
  // =========================================================================
  // Setup Endpoints
  // =========================================================================

  http.post('*/api/setup/session', () => {
    return HttpResponse.json({
      session_id: 'test-session-123',
      created_at: new Date().toISOString(),
    });
  }),

  http.post('*/api/setup/discover', () => {
    return HttpResponse.json({
      routers: [
        {
          ip: '192.168.50.1',
          type: 'ASUS',
          model: 'RT-AX86U',
          confidence: 0.95,
        },
        {
          ip: '192.168.50.2',
          type: 'Generic',
          model: 'UPnP Router',
          confidence: 0.7,
        },
      ],
    });
  }),

  http.post('*/api/setup/router-credentials', async ({ request }) => {
    const body = await request.json() as { router_ip: string; admin_username: string; admin_password: string };
    
    if (body.admin_password === 'wrong-password') {
      return HttpResponse.json(
        { detail: 'Authentication failed' },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      router: {
        ip: body.router_ip,
        vendor: 'ASUS',
        model: 'RT-AX86U',
        firmware_version: '3.0.0.4.386',
        connected_clients: 12,
      },
    });
  }),

  http.post('*/api/setup/connect', () => {
    return HttpResponse.json({
      success: true,
      message: 'Connected to router',
    });
  }),

  http.get('*/api/setup/status', () => {
    return HttpResponse.json({
      is_setup_complete: false,
      current_step: 1,
    });
  }),

  // =========================================================================
  // Device Endpoints
  // =========================================================================

  http.get('*/api/devices', ({ request }) => {
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const status = url.searchParams.get('containment_status');
    
    let devices = Array.from({ length: 10 }, (_, i) => generateDevice(i + 1));
    
    if (status) {
      devices = devices.filter(d => d.containment_status === status);
    }

    return HttpResponse.json({
      count: devices.length,
      devices: devices.slice(0, limit),
    });
  }),

  http.get('*/api/devices/:id', ({ params }) => {
    const deviceId = params.id as string;
    const id = parseInt(deviceId.replace('device-', ''), 10);
    
    if (isNaN(id) || id < 1) {
      return HttpResponse.json(
        { detail: 'Device not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      device: generateDevice(id),
      history: [],
    });
  }),

  http.patch('*/api/devices/:id', async ({ params, request }) => {
    const deviceId = params.id as string;
    const body = await request.json();
    
    return HttpResponse.json({
      device: generateDevice(1, { id: deviceId, ...body }),
      updated: true,
    });
  }),

  http.delete('*/api/devices/:id', ({ params }) => {
    const deviceId = params.id as string;
    
    return HttpResponse.json({
      deleted: true,
      device_id: deviceId,
    });
  }),

  http.post('*/api/devices/:id/contain', ({ params }) => {
    const deviceId = params.id as string;
    
    return HttpResponse.json({
      success: true,
      device_id: deviceId,
      containment_status: 'contained',
    });
  }),

  http.post('*/api/devices/:id/release', ({ params }) => {
    const deviceId = params.id as string;
    
    return HttpResponse.json({
      success: true,
      device_id: deviceId,
      containment_status: 'released',
    });
  }),

  // =========================================================================
  // Alert Endpoints
  // =========================================================================

  http.get('*/api/alerts', ({ request }) => {
    const url = new URL(request.url);
    const severity = url.searchParams.get('severity');
    const status = url.searchParams.get('status');
    
    let alerts = [
      generateAlert(1, { acknowledged: false, severity: 'critical' }),
      generateAlert(2, { acknowledged: false, severity: 'high' }),
      generateAlert(3, { acknowledged: false, severity: 'medium' }),
      generateAlert(4, { acknowledged: true, severity: 'low' }),
      generateAlert(5, { acknowledged: true, severity: 'info' }),
    ];
    
    if (severity) {
      alerts = alerts.filter(a => a.severity === severity);
    }
    
    if (status === 'unacknowledged') {
      alerts = alerts.filter(a => !a.acknowledged);
    }

    const newCount = alerts.filter(a => !a.acknowledged).length;

    return HttpResponse.json({
      alerts,
      new_count: newCount,
      acknowledged_count: alerts.length - newCount,
    });
  }),

  http.post('*/api/alerts/:id/acknowledge', ({ params }) => {
    const alertId = params.id as string;
    
    return HttpResponse.json({
      acknowledged: true,
      alert_id: alertId,
      acknowledged_at: new Date().toISOString(),
    });
  }),

  http.post('*/api/alerts/acknowledge-all', () => {
    return HttpResponse.json({
      acknowledged: true,
      count: 3,
    });
  }),

  // =========================================================================
  // Security Event Endpoints
  // =========================================================================

  http.get('*/api/security/events', ({ request }) => {
    const url = new URL(request.url);
    const agent = url.searchParams.get('agent');
    const severity = url.searchParams.get('severity');
    const eventType = url.searchParams.get('eventType');
    
    let events = Array.from({ length: 15 }, (_, i) => generateEvent(i + 1));
    
    if (agent) {
      events = events.filter(e => e.agent === agent);
    }
    if (severity) {
      events = events.filter(e => e.severity === severity);
    }
    if (eventType) {
      events = events.filter(e => e.event_type === eventType);
    }

    return HttpResponse.json({
      events,
      total: events.length,
    });
  }),

  http.get('*/api/security/blocked-stats', () => {
    return HttpResponse.json({
      total_blocked: 42,
      today_blocked: 5,
      by_category: {
        'unauthorized_access': 15,
        'policy_violation': 18,
        'anomaly_detected': 9,
      },
      trend: 'decreasing',
    });
  }),

  http.get('*/api/security/tool-usage', ({ request }) => {
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || '24h';
    
    return HttpResponse.json({
      period,
      data: [
        { tool: 'file_access', count: 120, period },
        { tool: 'network_scan', count: 45, period },
        { tool: 'memory_access', count: 89, period },
      ],
    });
  }),

  http.get('*/api/security/memory-access', () => {
    return HttpResponse.json({
      data: [
        { agent: 'agent-1', level: 'critical', count: 15 },
        { agent: 'agent-2', level: 'high', count: 23 },
        { agent: 'agent-3', level: 'medium', count: 8 },
        { agent: 'agent-1', level: 'low', count: 45 },
      ],
    });
  }),

  // =========================================================================
  // Agent Endpoints
  // =========================================================================

  http.get('*/api/agents', () => {
    const agents = Array.from({ length: 3 }, (_, i) => generateAgent(i + 1));
    
    return HttpResponse.json({
      agents,
      total: agents.length,
      online_count: agents.filter(a => a.status === 'ONLINE').length,
    });
  }),

  http.get('*/api/agents/:id', ({ params }) => {
    const agentId = params.id as string;
    const id = parseInt(agentId.replace('agent-', ''), 10);
    
    return HttpResponse.json({
      agent: generateAgent(id || 1),
    });
  }),

  http.post('*/api/agents/:id/heartbeat', ({ params }) => {
    const agentId = params.id as string;
    
    return HttpResponse.json({
      acknowledged: true,
      agent_id: agentId,
    });
  }),

  // =========================================================================
  // Discovery Endpoints
  // =========================================================================

  http.post('*/api/discovery/scan', () => {
    return HttpResponse.json({
      scan_id: 'scan-123',
      status: 'started',
      estimated_duration: 60,
    });
  }),

  http.get('*/api/discovery/status/:scan_id', ({ params }) => {
    const scanId = params.scan_id as string;
    
    return HttpResponse.json({
      scan_id: scanId,
      status: 'completed',
      progress: 100,
      devices_found: 8,
      completed_at: new Date().toISOString(),
    });
  }),

  // =========================================================================
  // Health Endpoint
  // =========================================================================

  http.get('*/api/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      services: {
        database: 'connected',
        redis: 'connected',
        discovery: 'running',
      },
    });
  }),

  // =========================================================================
  // SSE Event Stream
  // =========================================================================

  http.get('*/api/events/stream', () => {
    // Return empty stream for tests
    return new HttpResponse('data: {"type": "connected"}\n\n', {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }),

  // =========================================================================
  // Error Handlers for Testing Error States
  // =========================================================================

  http.get('*/api/error/500', () => {
    return HttpResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }),

  http.get('*/api/error/timeout', () => {
    return HttpResponse.json(
      { detail: 'Request timeout' },
      { status: 408 }
    );
  }),

  http.get('*/api/error/network', () => {
    return HttpResponse.error();
  }),
];

// ============================================================================
// Scenario-Specific Handler Sets
// ============================================================================

export const emptyHandlers = [
  http.get('*/api/devices', () => HttpResponse.json({ count: 0, devices: [] })),
  http.get('*/api/alerts', () => HttpResponse.json({ alerts: [], new_count: 0, acknowledged_count: 0 })),
  http.get('*/api/security/events', () => HttpResponse.json({ events: [], total: 0 })),
];

export const errorHandlers = [
  http.get('*/api/devices', () =>
    HttpResponse.json({ detail: 'Database connection failed' }, { status: 500 })
  ),
  http.get('*/api/alerts', () =>
    HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
  ),
];

export const slowHandlers = [
  http.get('*/api/devices', async () => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return HttpResponse.json({
      count: 5,
      devices: Array.from({ length: 5 }, (_, i) => generateDevice(i + 1)),
    });
  }),
];

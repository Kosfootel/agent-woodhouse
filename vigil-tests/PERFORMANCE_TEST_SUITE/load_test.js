/**
 * Vigil Dashboard - Load Testing Script
 * 
 * This k6 script performs load testing to verify system behavior
 * under expected normal load conditions.
 * 
 * Usage:
 *   k6 run --env API_URL=http://localhost:8000/api/v2 load_test.js
 * 
 * Or with more options:
 *   k6 run --vus 50 --duration 5m --env API_URL=http://localhost:8000/api/v2 load_test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Environment configuration
const API_URL = __ENV.API_URL || 'http://localhost:8000/api/v2';
const FRONTEND_URL = __ENV.FRONTEND_URL || 'http://localhost:3000';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const successfulLogins = new Counter('successful_logins');
const failedRequests = new Counter('failed_requests');
const activeDevices = new Gauge('active_devices');
const dbConnectionErrors = new Counter('db_connection_errors');

// Test configuration - Normal load
export const options = {
  scenarios: {
    // Normal user load - steady traffic
    steady_load: {
      executor: 'constant-vus',
      vus: 20,
      duration: '5m',
      startTime: '0s',
    },
    // Ramp up to simulate growing load
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up to 50 VUs
        { duration: '3m', target: 50 },   // Stay at 50 VUs
        { duration: '2m', target: 0 },    // Ramp down
      ],
      startTime: '1m',
    },
    // Spike test - sudden increase
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 100 },  // Spike to 100 VUs
        { duration: '1m', target: 100 },    // Hold spike
        { duration: '30s', target: 0 },     // Return to normal
      ],
      startTime: '8m',
    },
  },
  thresholds: {
    // Performance thresholds
    http_req_duration: ['p(95)<2000'],     // 95% of requests under 2s
    http_req_duration: ['p(99)<5000'],     // 99% of requests under 5s
    http_req_failed: ['rate<0.05'],         // Less than 5% failure rate
    errors: ['rate<0.05'],
    api_latency: ['p(95)<2000'],
    
    // Dashboard-specific endpoints
    'http_req_duration{name:dashboard_stats}': ['p(95)<1000'],
    'http_req_duration{name:device_list}': ['p(95)<1500'],
    'http_req_duration{name:alert_list}': ['p(95)<1000'],
  },
};

// Test data
const DEVICE_TYPES = ['phone', 'laptop', 'desktop', 'tablet', 'iot', 'tv', 'speaker', 'unknown'];
const CONTAINMENT_STATUSES = ['observing', 'blocked', 'trusted', 'quarantined'];
const EVENT_TYPES = ['device_joined', 'device_left', 'device_blocked', 'device_unblocked', 'alert_triggered', 'scan_complete'];

// Generate random MAC address
function generateMac() {
  const hex = '0123456789ABCDEF';
  let mac = '';
  for (let i = 0; i < 6; i++) {
    mac += hex[Math.floor(Math.random() * 16)];
    mac += hex[Math.floor(Math.random() * 16)];
    if (i < 5) mac += ':';
  }
  return mac;
}

// Generate random IP address
function generateIp() {
  return `192.168.50.${randomIntBetween(100, 254)}`;
}

// Main test function
export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    tags: {},
  };

  group('Public Endpoints', () => {
    // Health check - lightweight, frequent
    const healthStart = Date.now();
    const healthRes = http.get(`${API_URL}/health`, {
      ...params,
      tags: { name: 'health_check' },
    });
    apiLatency.add(Date.now() - healthStart, { endpoint: 'health' });
    
    check(healthRes, {
      'health status is 200': (r) => r.status === 200,
      'health response is valid': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.status === 'healthy' || body.status === 'degraded';
        } catch (e) {
          return false;
        }
      },
    }) || errorRate.add(1) && failedRequests.add(1);

    // Service info
    const infoRes = http.get(`${API_URL}/`, {
      ...params,
      tags: { name: 'service_info' },
    });
    
    check(infoRes, {
      'service info status is 200': (r) => r.status === 200,
    }) || errorRate.add(1) && failedRequests.add(1);

    sleep(randomIntBetween(1, 3));
  });

  group('Dashboard Data', () => {
    // Dashboard statistics
    const statsStart = Date.now();
    const statsRes = http.get(`${API_URL}/stats`, {
      ...params,
      tags: { name: 'dashboard_stats' },
    });
    apiLatency.add(Date.now() - statsStart, { endpoint: 'stats' });

    check(statsRes, {
      'stats status is 200': (r) => r.status === 200,
      'stats has required fields': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.device_count !== undefined &&
                 body.alert_count !== undefined &&
                 body.active_devices !== undefined;
        } catch (e) {
          return false;
        }
      },
    }) || errorRate.add(1) && failedRequests.add(1);

    // Store active devices count for gauge
    if (statsRes.status === 200) {
      try {
        const body = JSON.parse(statsRes.body);
        activeDevices.add(body.active_devices);
      } catch (e) {}
    }

    // Device list
    const devicesStart = Date.now();
    const devicesRes = http.get(`${API_URL}/devices?limit=25`, {
      ...params,
      tags: { name: 'device_list' },
    });
    apiLatency.add(Date.now() - devicesStart, { endpoint: 'devices' });

    check(devicesRes, {
      'device list status is 200': (r) => r.status === 200,
      'device list has pagination': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.devices !== undefined && body.total_count !== undefined;
        } catch (e) {
          return false;
        }
      },
    }) || errorRate.add(1) && failedRequests.add(1);

    // Alerts list
    const alertsStart = Date.now();
    const alertsRes = http.get(`${API_URL}/alerts?limit=25&acknowledged=false`, {
      ...params,
      tags: { name: 'alert_list' },
    });
    apiLatency.add(Date.now() - alertsStart, { endpoint: 'alerts' });

    check(alertsRes, {
      'alert list status is 200': (r) => r.status === 200,
    }) || errorRate.add(1) && failedRequests.add(1);

    // Events timeline
    const eventsRes = http.get(`${API_URL}/events?limit=25&hours=24`, {
      ...params,
      tags: { name: 'events_timeline' },
    });

    check(eventsRes, {
      'events status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(randomIntBetween(2, 5));
  });

  group('Device Operations', () => {
    // Get specific device (random ID between 1-100)
    const deviceId = randomIntBetween(1, 100);
    const deviceRes = http.get(`${API_URL}/devices/${deviceId}`, {
      ...params,
      tags: { name: 'device_detail' },
    });

    check(deviceRes, {
      'device detail returns valid status': (r) => r.status === 200 || r.status === 404,
    }) || errorRate.add(1);

    // Filter devices by status
    const statusFilter = randomItem(CONTAINMENT_STATUSES);
    const filteredRes = http.get(`${API_URL}/devices?status=${statusFilter}&limit=10`, {
      ...params,
      tags: { name: 'device_filter' },
    });

    check(filteredRes, {
      'device filter status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    // Search devices
    const searchTerm = randomItem(['AA:BB', '192.168', 'Test', 'Device']);
    const searchRes = http.get(`${API_URL}/devices?search=${encodeURIComponent(searchTerm)}&limit=10`, {
      ...params,
      tags: { name: 'device_search' },
    });

    check(searchRes, {
      'device search status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(randomIntBetween(2, 5));
  });

  group('Security Endpoints', () => {
    // Security events
    const securityRes = http.get(`${API_URL}/security/events?limit=25`, {
      ...params,
      tags: { name: 'security_events' },
    });

    check(securityRes, {
      'security events status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    // Blocked stats
    const blockedRes = http.get(`${API_URL}/security/blocked-stats`, {
      ...params,
      tags: { name: 'blocked_stats' },
    });

    check(blockedRes, {
      'blocked stats status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    // Anomalies
    const anomaliesRes = http.get(`${API_URL}/security/anomalies?limit=25`, {
      ...params,
      tags: { name: 'anomalies_list' },
    });

    check(anomaliesRes, {
      'anomalies status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(randomIntBetween(2, 5));
  });

  group('Write Operations (10% of time)', () => {
    // Only perform writes 10% of the time to simulate read-heavy workload
    if (Math.random() < 0.1) {
      // Announce a new agent/device
      const announceData = {
        name: `LoadTest-Agent-${__VU}-${Date.now()}`,
        ip: generateIp(),
        mac: generateMac(),
        agent_type: 'load_test',
        capabilities: ['monitoring'],
      };

      const announceRes = http.post(`${API_URL}/setup/agent/announce`, 
        JSON.stringify(announceData),
        { ...params, tags: { name: 'agent_announce' } }
      );

      check(announceRes, {
        'agent announce status is 200': (r) => r.status === 200,
        'agent created or updated': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.status === 'created' || body.status === 'updated';
          } catch (e) {
            return false;
          }
        },
      }) || errorRate.add(1) && failedRequests.add(1);

      // Log a security event
      const securityEvent = {
        agent_id: `load-test-agent-${__VU}`,
        tool_name: randomItem(['file_read', 'file_write', 'system_exec']),
        arguments: { path: '/test/path' },
        result: 'success',
      };

      const logRes = http.post(`${API_URL}/security/log-tool`,
        JSON.stringify(securityEvent),
        { ...params, tags: { name: 'log_security_event' } }
      );

      check(logRes, {
        'log security event status is 200': (r) => r.status === 200,
      }) || errorRate.add(1);

      sleep(randomIntBetween(3, 7));
    }
  });

  group('Setup Endpoints', () => {
    // Setup status
    const setupRes = http.get(`${API_URL}/setup/status`, {
      ...params,
      tags: { name: 'setup_status' },
    });

    check(setupRes, {
      'setup status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    // Router status
    const routerRes = http.get(`${API_URL}/setup/router-status`, {
      ...params,
      tags: { name: 'router_status' },
    });

    check(routerRes, {
      'router status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(randomIntBetween(1, 3));
  });

  // Overall pacing
  sleep(randomIntBetween(1, 3));
}

// Setup code runs once before the test
export function setup() {
  console.log(`Starting load test against: ${API_URL}`);
  
  // Verify API is accessible
  const res = http.get(`${API_URL}/health`);
  if (res.status !== 200) {
    console.error(`API health check failed: ${res.status}`);
    throw new Error('API is not ready');
  }
  
  console.log('API health check passed');
  
  return {
    apiUrl: API_URL,
    startTime: Date.now(),
  };
}

// Teardown code runs once after the test
export function teardown(data) {
  const duration = Date.now() - data.startTime;
  console.log(`Load test completed in ${duration}ms`);
}

// Handle summary at the end
export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
    'load-test-results.json': JSON.stringify(data, null, 2),
    'load-test-summary.html': generateHtmlSummary(data),
  };
}

// Simple text summary
function textSummary(data, options) {
  const indent = options.indent || '';
  const colors = options.enableColors !== false;
  
  const green = colors ? '\x1b[32m' : '';
  const red = colors ? '\x1b[31m' : '';
  const reset = colors ? '\x1b[0m' : '';
  
  let output = '\n';
  output += `${indent}╔═══════════════════════════════════════════════════╗\n`;
  output += `${indent}║           LOAD TEST SUMMARY                       ║\n`;
  output += `${indent}╚═══════════════════════════════════════════════════╝\n\n`;
  
  output += `${indent}Duration: ${formatDuration(data.state.testRunDurationMs)}\n`;
  output += `${indent}Virtual Users: ${data.metrics.vus ? data.metrics.vus.max : 'N/A'}\n\n`;
  
  output += `${indent}Requests:\n`;
  output += `${indent}  Total: ${data.metrics.http_reqs ? data.metrics.http_reqs.count : 0}\n`;
  output += `${indent}  Failed: ${data.metrics.http_req_failed ? data.metrics.http_req_failed.passes : 0}\n`;
  
  if (data.metrics.http_req_duration) {
    const avg = data.metrics.http_req_duration.avg;
    const p95 = data.metrics.http_req_duration['p(95)'];
    const p99 = data.metrics.http_req_duration['p(99)'];
    
    const avgColor = avg < 1000 ? green : red;
    const p95Color = p95 < 2000 ? green : red;
    
    output += `${indent}Response Times:\n`;
    output += `${indent}  Average: ${avgColor}${avg.toFixed(2)}ms${reset}\n`;
    output += `${indent}  p(95): ${p95Color}${p95.toFixed(2)}ms${reset}\n`;
    output += `${indent}  p(99): ${p99.toFixed(2)}ms\n`;
  }
  
  output += '\n';
  
  return output;
}

function formatDuration(ms) {
  const minutes = Math.floor(ms / 60000);
  const seconds = ((ms % 60000) / 1000).toFixed(0);
  return `${minutes}m ${seconds}s`;
}

// Simple HTML summary generator
function generateHtmlSummary(data) {
  const title = 'Vigil Dashboard Load Test Results';
  const timestamp = new Date().toISOString();
  
  return `
<!DOCTYPE html>
<html>
<head>
  <title>${title}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    h1 { color: #333; }
    .metric { margin: 10px 0; }
    .pass { color: green; }
    .fail { color: red; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #4CAF50; color: white; }
    tr:nth-child(even) { background-color: #f2f2f2; }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <p>Generated: ${timestamp}</p>
  
  <h2>Overview</h2>
  <div class="metric">Duration: ${formatDuration(data.state.testRunDurationMs)}</div>
  <div class="metric">Total Requests: ${data.metrics.http_reqs ? data.metrics.http_reqs.count : 0}</div>
  <div class="metric">Failed Requests: ${data.metrics.http_req_failed ? data.metrics.http_req_failed.passes : 0}</div>
  
  <h2>Response Times</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Average</td><td>${data.metrics.http_req_duration ? data.metrics.http_req_duration.avg.toFixed(2) : 'N/A'} ms</td></tr>
    <tr><td>p(95)</td><td>${data.metrics.http_req_duration ? data.metrics.http_req_duration['p(95)'].toFixed(2) : 'N/A'} ms</td></tr>
    <tr><td>p(99)</td><td>${data.metrics.http_req_duration ? data.metrics.http_req_duration['p(99)'].toFixed(2) : 'N/A'} ms</td></tr>
    <tr><td>Min</td><td>${data.metrics.http_req_duration ? data.metrics.http_req_duration.min.toFixed(2) : 'N/A'} ms</td></tr>
    <tr><td>Max</td><td>${data.metrics.http_req_duration ? data.metrics.http_req_duration.max.toFixed(2) : 'N/A'} ms</td></tr>
  </table>
  
  <h2>Thresholds</h2>
  <table>
    <tr><th>Threshold</th><th>Status</th></tr>
    ${Object.entries(data.metrics).filter(([k]) => k.startsWith('http_req_duration') || k === 'http_req_failed').map(([k, v]) => {
      const passed = v.thresholds ? Object.values(v.thresholds).every(t => t.ok) : true;
      return `<tr><td>${k}</td><td class="${passed ? 'pass' : 'fail'}">${passed ? 'PASS' : 'FAIL'}</td></tr>`;
    }).join('')}
  </table>
</body>
</html>
  `;
}

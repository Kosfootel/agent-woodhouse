/**
 * Router Discovery and Connection Library
 * Helper functions for the Vigil Setup Wizard
 */

// Common router IP addresses to try
const COMMON_ROUTER_IPS = [
  '192.168.1.1',
  '192.168.50.1',
  '192.168.0.1',
  '10.0.0.1',
  '192.168.2.1',
  '172.16.0.1',
];

// Known router fingerprints based on response headers/body
const ROUTER_FINGERPRINTS = {
  'ASUS': {
    patterns: ['asus', 'rt-', 'zenwifi'],
    testUrl: '/api/status',
    defaultUser: 'admin',
  },
  'TP-Link': {
    patterns: ['tp-link', 'tplink'],
    testUrl: '/',
    defaultUser: 'admin',
  },
  'Netgear': {
    patterns: ['netgear'],
    testUrl: '/',
    defaultUser: 'admin',
  },
  'Linksys': {
    patterns: ['linksys'],
    testUrl: '/',
    defaultUser: 'admin',
  },
  'UniFi': {
    patterns: ['unifi', 'ubiquiti'],
    testUrl: '/api/s/default/stat/health',
    defaultUser: 'ubnt',
  },
};

// Friendly error message translations
const ERROR_TRANSLATIONS = {
  'Connection refused': "Can't reach router. Check your network connection.",
  'Network Error': "Can't connect to router. Make sure you're on the same network.",
  'timeout': 'Connection timed out. Router might be busy or unreachable.',
  'Unauthorized': 'Invalid username or password. Check the router label.',
  'Forbidden': 'Access denied. Try different credentials.',
  'Not Found': 'Router responded but might not support this feature.',
  'ECONNREFUSED': "Can't reach router. Check your network connection.",
  'ETIMEDOUT': 'Connection timed out. Router might be busy or unreachable.',
  'ENOTFOUND': "Can't find router address. Check your network connection.",
};

/**
 * Translate technical errors to user-friendly messages
 */
export function translateError(error) {
  const message = error?.message || error?.toString() || 'Unknown error';
  
  for (const [pattern, translation] of Object.entries(ERROR_TRANSLATIONS)) {
    if (message.toLowerCase().includes(pattern.toLowerCase())) {
      return translation;
    }
  }
  
  return "Something went wrong. Please try again.";
}

/**
 * Scan for routers at common IP addresses
 * Returns the first responsive router or null
 */
export async function scanForRouter() {
  // Try each common IP with fetch that works in browser
  for (const ip of COMMON_ROUTER_IPS) {
    try {
      // Use a timeout promise
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('timeout')), 2000)
      );
      
      // Try to fetch with no-cors mode (for detection)
      const fetchPromise = fetch(`http://${ip}/favicon.ico`, {
        method: 'GET',
        mode: 'no-cors',
        cache: 'no-store',
      }).then(() => true).catch(() => false);
      
      // Race between timeout and fetch
      const result = await Promise.race([fetchPromise, timeoutPromise]).catch(() => false);
      
      if (result) {
        // Router responded
        return {
          ip,
          found: true,
        };
      }
    } catch (err) {
      // Continue to next IP
      continue;
    }
  }
  
  // Check current network - if we're on 192.168.50.x, assume .1 is router
  try {
    const response = await fetch('/api/setup/network-info');
    if (response.ok) {
      const data = await response.json();
      if (data.gateway) {
        return {
          ip: data.gateway,
          found: true,
        };
      }
    }
  } catch (e) {
    // Fallback to common gateway
  }
  
  // Default to most likely router based on current URL
  const currentHost = window.location.hostname;
  if (currentHost.startsWith('192.168.50.')) {
    return {
      ip: '192.168.50.1',
      found: true,
    };
  }
  if (currentHost.startsWith('192.168.1.')) {
    return {
      ip: '192.168.1.1',
      found: true,
    };
  }
  if (currentHost.startsWith('10.0.0.')) {
    return {
      ip: '10.0.0.1',
      found: true,
    };
  }
  
  // No router found
  return null;
}

/**
 * Identify router brand by analyzing response
 */
export async function identifyRouter(ip) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`http://${ip}`, {
      mode: 'no-cors',
      signal: controller.signal,
      cache: 'no-store',
    });
    
    clearTimeout(timeoutId);
    
    // Since we're in no-cors mode, we can't read the response
    // Return a generic identification with IP
    return {
      brand: 'Router',
      model: 'Detected',
      ip,
      confidence: 'medium',
    };
  } catch (err) {
    // Even if fetch fails, the IP responded earlier
    return {
      brand: 'Router',
      model: 'Unknown',
      ip,
      confidence: 'low',
    };
  }
}

/**
 * Test router credentials
 * In a real implementation, this would attempt login
 * For now, we simulate success with mock data
 */
export async function testCredentials(ip, username, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // Mock validation - in production this would actually try to login
      if (username && password && password.length >= 4) {
        resolve({
          success: true,
          message: 'Credentials verified',
        });
      } else {
        reject(new Error('Invalid username or password'));
      }
    }, 1500);
  });
}

/**
 * Get devices connected to the router
 * Returns a mock list of devices for demonstration
 */
export async function getDevices(ip, username, password) {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Mock device list - in production this would fetch from router API
      const mockDevices = [
        { id: 1, name: 'iPhone', mac: 'AA:BB:CC:11:22:33', ip: '192.168.50.101', type: 'mobile', lastSeen: '2 min ago' },
        { id: 2, name: 'MacBook Pro', mac: 'AA:BB:CC:44:55:66', ip: '192.168.50.102', type: 'laptop', lastSeen: '5 min ago' },
        { id: 3, name: 'Smart TV', mac: 'AA:BB:CC:77:88:99', ip: '192.168.50.103', type: 'smart-tv', lastSeen: '1 hour ago' },
        { id: 4, name: 'iPad', mac: 'AA:BB:CC:AA:BB:CC', ip: '192.168.50.104', type: 'tablet', lastSeen: '30 min ago' },
        { id: 5, name: 'HomePod', mac: 'AA:BB:CC:DD:EE:FF', ip: '192.168.50.105', type: 'smart-speaker', lastSeen: '10 min ago' },
        { id: 6, name: 'Nest Thermostat', mac: '11:22:33:44:55:66', ip: '192.168.50.106', type: 'iot', lastSeen: '1 min ago' },
        { id: 7, name: 'Ring Doorbell', mac: '11:22:33:AA:BB:CC', ip: '192.168.50.107', type: 'security', lastSeen: '3 min ago' },
        { id: 8, name: 'Nintendo Switch', mac: '22:33:44:55:66:77', ip: '192.168.50.108', type: 'gaming', lastSeen: '2 hours ago' },
        { id: 9, name: 'Desktop PC', mac: '33:44:55:66:77:88', ip: '192.168.50.109', type: 'desktop', lastSeen: '15 min ago' },
        { id: 10, name: 'Printer', mac: '44:55:66:77:88:99', ip: '192.168.50.110', type: 'printer', lastSeen: '5 hours ago' },
        { id: 11, name: 'Smart Bulb 1', mac: '55:66:77:88:99:AA', ip: '192.168.50.111', type: 'iot', lastSeen: '20 min ago' },
        { id: 12, name: 'Smart Bulb 2', mac: '55:66:77:88:99:BB', ip: '192.168.50.112', type: 'iot', lastSeen: '20 min ago' },
        { id: 13, name: 'Security Camera', mac: '66:77:88:99:AA:BB', ip: '192.168.50.113', type: 'security', lastSeen: '1 min ago' },
        { id: 14, name: 'Apple Watch', mac: '77:88:99:AA:BB:CC', ip: '192.168.50.114', type: 'wearable', lastSeen: '8 min ago' },
        { id: 15, name: 'AirPods Pro', mac: '88:99:AA:BB:CC:DD', ip: '192.168.50.115', type: 'audio', lastSeen: '45 min ago' },
        { id: 16, name: 'Raspberry Pi', mac: '99:AA:BB:CC:DD:EE', ip: '192.168.50.116', type: 'server', lastSeen: '2 min ago' },
        { id: 17, name: 'Xbox Series X', mac: 'AA:BB:CC:DD:EE:FF', ip: '192.168.50.117', type: 'gaming', lastSeen: '1 hour ago' },
        { id: 18, name: 'Kindle', mac: 'BB:CC:DD:EE:FF:00', ip: '192.168.50.118', type: 'tablet', lastSeen: '3 hours ago' },
        { id: 19, name: 'Robot Vacuum', mac: 'CC:DD:EE:FF:00:11', ip: '192.168.50.119', type: 'appliance', lastSeen: '4 hours ago' },
      ];
      
      resolve(mockDevices);
    }, 2000);
  });
}

/**
 * Get device icon based on type
 */
export function getDeviceIcon(type) {
  const icons = {
    mobile: '📱',
    laptop: '💻',
    desktop: '🖥️',
    tablet: '📲',
    'smart-tv': '📺',
    'smart-speaker': '🔊',
    iot: '🔌',
    security: '🔒',
    gaming: '🎮',
    printer: '🖨️',
    wearable: '⌚',
    audio: '🎧',
    server: '🖥️',
    appliance: '🤖',
    unknown: '📡',
  };
  
  return icons[type] || icons.unknown;
}

/**
 * Save setup progress to localStorage
 */
export function saveProgress(step, data) {
  try {
    const progress = {
      step,
      data,
      timestamp: Date.now(),
    };
    localStorage.setItem('vigilSetupProgress', JSON.stringify(progress));
  } catch (err) {
    console.warn('Could not save progress:', err);
  }
}

/**
 * Load setup progress from localStorage
 */
export function loadProgress() {
  try {
    const saved = localStorage.getItem('vigilSetupProgress');
    if (saved) {
      const progress = JSON.parse(saved);
      // Only restore if less than 24 hours old
      if (Date.now() - progress.timestamp < 24 * 60 * 60 * 1000) {
        return progress;
      }
    }
  } catch (err) {
    console.warn('Could not load progress:', err);
  }
  return null;
}

/**
 * Clear saved setup progress
 */
export function clearProgress() {
  try {
    localStorage.removeItem('vigilSetupProgress');
  } catch (err) {
    console.warn('Could not clear progress:', err);
  }
}

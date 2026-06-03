/**
 * Router Discovery Library (Simplified - No Credentials Required)
 * Helper functions for the Vigil Setup Wizard
 * 
 * Router API integration removed - ARP-based discovery only
 * See docs/ROUTER_INTEGRATION_DECISION.md for details
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

// Friendly error message translations
const ERROR_TRANSLATIONS = {
  'Connection refused': "Can't reach router. Check your network connection.",
  'Network Error': "Can't connect to router. Make sure you're on the same network.",
  'timeout': 'Connection timed out. Router might be busy or unreachable.',
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
 * Scan for router at common IP addresses
 * Returns the first responsive router or null
 */
export async function scanForRouter() {
  // Try each common IP
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
 * Identify router - simplified version
 * Returns basic info about the router
 */
export async function identifyRouter(ip) {
  // Simple identification based on IP
  return {
    brand: 'Network',
    model: 'Router',
    ip,
    confidence: 'medium',
  };
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

// NOTE: testCredentials() and getDevices() removed
// These are now handled by the backend API which uses ARP-based discovery
// See docs/ROUTER_INTEGRATION_DECISION.md for architecture details

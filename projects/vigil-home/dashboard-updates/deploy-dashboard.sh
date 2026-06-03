#!/bin/bash
# Deploy dashboard updates for Vigil Phase 1

set -e

echo "=== Vigil Dashboard Update - Phase 1: Device Identity ==="

# Backup existing files
echo "Creating backup..."
cd /opt/vigil-dashboard
cp src/lib/types.ts src/lib/types.ts.backup.$(date +%Y%m%d%H%M%S)
cp src/lib/api.ts src/lib/api.ts.backup.$(date +%Y%m%d%H%M%S)

echo "Updating types.ts..."
cat > src/lib/types.ts << 'EOF'
// Updated types for Vigil Dashboard - Phase 1: Device Identity

export interface Device {
  id: string;
  mac: string;
  ip: string;
  hostname: string | null;
  device_type: string | null;
  trust_score: number;
  // Device identity fields
  nickname: string | null;
  icon_type: string | null;
  containment_status: "trusted" | "blocked" | "observing" | "pending_review";
  user_trust_override: boolean;
  vendor: string | null;
  classified_type: string | null;
  classified_confidence: number | null;
  first_seen: string;
  last_seen: string;
  online: boolean;
  confidence?: number;
  behavior?: DeviceBehavior;
}

export interface DeviceBehavior {
  normal_hours: string;
  normal_connections: number;
  bandwidth_pattern: string;
}

// Display name helper - use nickname if available
export const getDeviceDisplayName = (device: Device): string => {
  if (device.nickname) return device.nickname;
  if (device.hostname) return device.hostname;
  if (device.vendor) return `${device.vendor} Device`;
  return `Device ${device.mac.slice(-5)}`;
};

// Device icon mapping
export const getDeviceIcon = (iconType: string | null): string => {
  const icons: Record<string, string> = {
    smartphone: "📱",
    laptop: "💻",
    desktop: "🖥️",
    tv: "📺",
    camera: "📷",
    router: "📡",
    server: "🖥️",
    device: "🔌",
  };
  return icons[iconType || "device"] || "🔌";
};

// Trust status helpers
export const getTrustColor = (score: number): string => {
  if (score >= 0.8) return "text-emerald-500";
  if (score >= 0.5) return "text-amber-500";
  return "text-rose-500";
};

export const getTrustLabel = (score: number): string => {
  if (score >= 0.8) return "Trusted";
  if (score >= 0.5) return "Neutral";
  return "Suspicious";
};

export const getTrustBg = (score: number): string => {
  if (score >= 0.8) return "bg-emerald-500/10 border-emerald-500/20";
  if (score >= 0.5) return "bg-amber-500/10 border-amber-500/20";
  return "bg-rose-500/10 border-rose-500/20";
};

// Containment status helpers
export const getContainmentStatus = (status: string): { label: string; color: string; icon: string } => {
  switch (status) {
    case "trusted":
      return { label: "Trusted", color: "text-emerald-500", icon: "✓" };
    case "blocked":
      return { label: "Blocked", color: "text-rose-500", icon: "✕" };
    case "observing":
      return { label: "Watching", color: "text-amber-500", icon: "👁" };
    default:
      return { label: "Unknown", color: "text-slate-500", icon: "?" };
  }
};

export interface Alert {
  id: string;
  severity: "critical" | "warning" | "info";
  title: string;
  description: string;
  timestamp: string;
  device_id?: string;
  acknowledged: boolean;
}

export interface Event {
  id: string;
  device_id: string;
  device_name: string;
  event_type: string;
  description: string;
  timestamp: string;
}

export interface TrustTrend {
  date: string;
  score: number;
}

export interface DeviceTypeCount {
  type: string;
  count: number;
}

export interface AlertVolume {
  date: string;
  critical: number;
  warning: number;
  info: number;
}

export interface TopTalker {
  device_id: string;
  device_name: string;
  mac: string;
  events: number;
}

export interface NetworkSummary {
  trust_score: number;
  trust_trend: "up" | "down" | "stable";
  total_devices: number;
  new_today: number;
  offline: number;
  alerts_critical: number;
  alerts_warning: number;
  alerts_info: number;
}
EOF

echo "Updating api.ts with new device management functions..."

# Append new API functions to api.ts
cat >> src/lib/api.ts << 'EOF'

// Device management API functions

export async function updateDeviceNickname(
  deviceId: string,
  nickname: string
): Promise<{ message: string; device: Device }> {
  return fetchApi(`/devices/${deviceId}/nickname`, {
    method: "PATCH",
    body: JSON.stringify({ nickname }),
  });
}

export async function trustDevice(deviceId: string): Promise<{ message: string; device: Device }> {
  return fetchApi(`/devices/${deviceId}/trust`, {
    method: "POST",
  });
}

export async function blockDevice(deviceId: string): Promise<{ message: string; device: Device }> {
  return fetchApi(`/devices/${deviceId}/block`, {
    method: "POST",
  });
}

export async function unblockDevice(deviceId: string): Promise<{ message: string; device: Device }> {
  return fetchApi(`/devices/${deviceId}/unblock`, {
    method: "POST",
  });
}

export interface DeviceBehaviorData {
  device_id: number;
  typical_hours: number[];
  connection_pattern: string;
  avg_bandwidth_mbps: number | null;
  peak_bandwidth_mbps: number | null;
  event_count_7d: number;
  behavior_summary: string;
}

export async function fetchDeviceBehavior(
  deviceId: string
): Promise<DeviceBehaviorData> {
  return fetchApi(`/devices/${deviceId}/behavior`);
}
EOF

echo "Building dashboard..."
npm run build

echo "=== Dashboard Update Complete ==="
echo "New features available:"
echo "  - Device nicknames"
echo "  - Device icons"
echo "  - Trust/Block actions"
echo "  - Behavioral analysis"

export interface Device {
  id: string;
  mac: string;
  ip: string;
  name: string;
  device_type: string;
  trust_score: number;
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

// ── Backend API response shapes ────────────────────────────────
// These match the FastAPI backend models (models.py to_dict() output).

export interface BackendDevice {
  id: number;
  mac: string;
  ip: string;
  hostname: string | null;
  device_type: string | null;
  trust_score: number;
  classified_type: string | null;
  classified_confidence: number | null;
  first_seen: string;
  last_seen: string;
}

export interface BackendAlert {
  id: number;
  device_id: number;
  timestamp: string;
  alert_type: string;
  severity: string;
  narrative: string | null;
  status: string;
  acknowledged: boolean;
}

export interface BackendEvent {
  id: number;
  device_id: number;
  timestamp: string;
  event_type: string;
  severity: string;
  details: Record<string, unknown> | null;
}

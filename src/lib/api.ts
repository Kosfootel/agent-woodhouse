// API_BASE can be overridden via env var for different deploy targets
// Production (bettermachine-host): "/api" (proxied by nginx to GX-10)
// Direct (GX-10): "http://192.168.50.30:8000"
const API_BASE = process.env.VIGIL_API_BASE || "http://192.168.50.30:8000";

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText} for ${endpoint}`);
  }

  return res.json();
}

import type {
  Device,
  Alert,
  Event,
  NetworkSummary,
  TrustTrend,
  DeviceTypeCount,
  AlertVolume,
  TopTalker,
  BackendDevice,
  BackendAlert,
  BackendEvent,
} from "./types";

export async function fetchDevices(): Promise<Device[]> {
  const data = await fetchApi<{ count: number; devices: BackendDevice[] }>("/devices");
  return (data.devices || []).map((d: BackendDevice) => ({
    id: String(d.id),
    mac: d.mac,
    ip: d.ip,
    name: d.hostname || d.mac,
    device_type: d.device_type || "unknown",
    trust_score: d.trust_score ?? 0.5,
    first_seen: d.first_seen,
    last_seen: d.last_seen,
    online: "online" in d ? Boolean((d as { online?: boolean }).online) : true,
    confidence: d.classified_confidence ?? undefined,
    behavior: undefined,
  }));
}

export async function fetchDevice(id: string): Promise<Device> {
  const d: BackendDevice & { recent_events?: BackendEvent[]; open_alerts?: BackendAlert[] } = await fetchApi(`/devices/${id}`);
  return {
    id: String(d.id),
    mac: d.mac,
    ip: d.ip,
    name: d.hostname || d.mac,
    device_type: d.device_type || "unknown",
    trust_score: d.trust_score ?? 0.5,
    first_seen: d.first_seen,
    last_seen: d.last_seen,
    online: "online" in d ? Boolean((d as { online?: boolean }).online) : true,
    confidence: d.classified_confidence ?? undefined,
    behavior: undefined,
  };
}

export async function classifyDevice(mac: string): Promise<{
  device_type: string;
  confidence: number;
}> {
  return fetchApi(`/classify/${mac}`);
}

export async function markAsTrusted(device: Device): Promise<void> {
  return fetchApi("/baseline", {
    method: "POST",
    body: JSON.stringify({
      mac: device.mac,
      ip: device.ip,
      hostname: device.name,
      device_type: device.device_type,
    }),
  });
}

export async function fetchAlerts(): Promise<Alert[]> {
  const data = await fetchApi<{ count: number; alerts: BackendAlert[] }>("/alerts");
  // Map backend response fields to frontend Alert interface
  return (data.alerts || []).map((a: BackendAlert) => ({
    id: String(a.id),
    severity: a.severity === "high" || a.severity === "critical" ? "critical" as const : a.severity === "medium" ? "warning" as const : "info" as const,
    title: a.alert_type || "Alert",
    description: a.narrative || "No details available",
    timestamp: a.timestamp,
    device_id: a.device_id != null ? String(a.device_id) : undefined,
    acknowledged: a.acknowledged === true,
  }));
}

export async function acknowledgeAlert(alertId: string | number): Promise<void> {
  await fetchApi(`/alerts/${alertId}/acknowledge`, {
    method: "PATCH",
  });
}

export async function unacknowledgeAlert(alertId: string | number): Promise<void> {
  await fetchApi(`/alerts/${alertId}/unacknowledge`, {
    method: "PATCH",
  });
}

export async function fetchEvents(): Promise<Event[]> {
  const data = await fetchApi<{ count: number; events: BackendEvent[] }>("/events");
  return (data.events || []).map((e: BackendEvent) => ({
    id: String(e.id),
    device_id: String(e.device_id),
    device_name: (e.details as Record<string, string>)?.device_name || "",
    event_type: e.event_type,
    description: (e.details as Record<string, string>)?.description || e.event_type,
    timestamp: e.timestamp,
  }));
}

export async function fetchNetworkSummary(): Promise<NetworkSummary> {
  try {
    const [devices, alerts] = await Promise.all([
      fetchDevices(),
      fetchAlerts(),
    ]);

    const total = devices.length;
    const online = devices.filter((d) => d.online).length;
    const offline = total - online;

    // Count new devices today
    const today = new Date().toISOString().split("T")[0];
    const newToday = devices.filter((d) => {
      const firstSeen = d.first_seen?.split("T")[0];
      return firstSeen === today;
    }).length;

    // Aggregate trust score
    const avgTrust =
      devices.length > 0
        ? devices.reduce((sum, d) => sum + d.trust_score, 0) / devices.length
        : 0;

    const critical = alerts.filter((a) => a.severity === "critical").length;
    const warning = alerts.filter((a) => a.severity === "warning").length;
    const info = alerts.filter((a) => a.severity === "info").length;

    // Determine trend (compare with first device's score as baseline)
    const trustTrend: "up" | "down" | "stable" =
      avgTrust > 0.7 ? "up" : avgTrust > 0.4 ? "stable" : "down";

    return {
      trust_score: Math.round(avgTrust * 100) / 100,
      trust_trend: trustTrend,
      total_devices: total,
      new_today: newToday,
      offline,
      alerts_critical: critical,
      alerts_warning: warning,
      alerts_info: info,
    };
  } catch {
    return {
      trust_score: 0,
      trust_trend: "stable",
      total_devices: 0,
      new_today: 0,
      offline: 0,
      alerts_critical: 0,
      alerts_warning: 0,
      alerts_info: 0,
    };
  }
}

export async function fetchTrustTrend(
  days: number = 7
): Promise<TrustTrend[]> {
  try {
    // const events = await fetchEvents();
    // Simulate trust trend from events if actual endpoint not available
    const data: TrustTrend[] = [];
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      data.push({
        date: d.toISOString().split("T")[0],
        score: 0.5 + Math.random() * 0.4,
      });
    }
    return data;
  } catch {
    return [];
  }
}

export async function fetchDeviceTypeBreakdown(): Promise<DeviceTypeCount[]> {
  try {
    const devices = await fetchDevices();
    const counts: Record<string, number> = {};
    for (const d of devices) {
      counts[d.device_type] = (counts[d.device_type] || 0) + 1;
    }
    return Object.entries(counts).map(([type, count]) => ({ type, count }));
  } catch {
    return [];
  }
}

export async function fetchAlertVolume(): Promise<AlertVolume[]> {
  try {
    const alerts = await fetchAlerts();
    const volume: Record<string, AlertVolume> = {};
    for (const a of alerts) {
      const date = a.timestamp.split("T")[0];
      if (!volume[date]) {
        volume[date] = { date, critical: 0, warning: 0, info: 0 };
      }
      volume[date][a.severity]++;
    }
    return Object.values(volume).sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  } catch {
    return [];
  }
}

export async function fetchTopTalkers(): Promise<TopTalker[]> {
  try {
    const evts = await fetchEvents();
    const counts: Record<
      string,
      { device_name: string; mac: string; count: number }
    > = {};
    for (const e of evts) {
      if (!counts[e.device_id]) {
        counts[e.device_id] = {
          device_name: e.device_name,
          mac: "",
          count: 0,
        };
      }
      counts[e.device_id].count++;
    }
    return Object.entries(counts)
      .map(([device_id, data]) => ({
        device_id,
        device_name: data.device_name,
        mac: data.mac,
        events: data.count,
      }))
      .sort((a, b) => b.events - a.events)
      .slice(0, 10);
  } catch {
    return [];
  }
}

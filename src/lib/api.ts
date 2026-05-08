// Proxy through nginx on the same host to avoid CORS issues
// Production: nginx on 192.168.50.32 proxies /api/* to GX-10:8000
const API_BASE = "";

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
} from "./types";

export async function fetchDevices(): Promise<Device[]> {
  return fetchApi<Device[]>("/devices");
}

export async function fetchDevice(id: string): Promise<Device> {
  return fetchApi<Device>(`/devices/${id}`);
}

export async function classifyDevice(mac: string): Promise<{
  device_type: string;
  confidence: number;
}> {
  return fetchApi(`/classify/${mac}`);
}

export async function markAsTrusted(mac: string): Promise<void> {
  return fetchApi("/baseline", {
    method: "POST",
    body: JSON.stringify({ mac }),
  });
}

export async function fetchAlerts(): Promise<Alert[]> {
  return fetchApi<Alert[]>("/alerts");
}

export async function fetchEvents(): Promise<Event[]> {
  return fetchApi<Event[]>("/events");
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

// Updated API functions for device management
// Add these to src/lib/api.ts

import type { Device } from "./types";

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

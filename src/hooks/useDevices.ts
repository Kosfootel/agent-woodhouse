"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchDevices,
  fetchDevice,
  fetchAlerts,
  fetchEvents,
  markAsTrusted,
  fetchNetworkSummary,
  fetchTrustTrend,
  fetchDeviceTypeBreakdown,
  fetchAlertVolume,
  fetchTopTalkers,
} from "@/lib/api";
import type { Device } from "@/lib/types";
export function useDevices() {
  return useQuery({
    queryKey: ["devices"],
    queryFn: fetchDevices,
    refetchInterval: 30000,
  });
}

export function useDevice(id: string) {
  return useQuery({
    queryKey: ["device", id],
    queryFn: () => fetchDevice(id),
    enabled: !!id,
    refetchInterval: 30000,
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 30000,
  });
}

export function useEvents() {
  return useQuery({
    queryKey: ["events"],
    queryFn: fetchEvents,
    refetchInterval: 30000,
  });
}

export function useNetworkSummary() {
  return useQuery({
    queryKey: ["networkSummary"],
    queryFn: fetchNetworkSummary,
    refetchInterval: 30000,
  });
}

export function useTrustTrend(days: number = 7) {
  return useQuery({
    queryKey: ["trustTrend", days],
    queryFn: () => fetchTrustTrend(days),
    refetchInterval: 60000,
  });
}

export function useDeviceTypeBreakdown() {
  return useQuery({
    queryKey: ["deviceTypeBreakdown"],
    queryFn: fetchDeviceTypeBreakdown,
    refetchInterval: 60000,
  });
}

export function useAlertVolume() {
  return useQuery({
    queryKey: ["alertVolume"],
    queryFn: fetchAlertVolume,
    refetchInterval: 60000,
  });
}

export function useTopTalkers() {
  return useQuery({
    queryKey: ["topTalkers"],
    queryFn: fetchTopTalkers,
    refetchInterval: 60000,
  });
}

export function useMarkAsTrusted() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (device: Device) => markAsTrusted(device.mac),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["networkSummary"] });
    },
  });
}

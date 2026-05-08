"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import TrustScore from "@/components/ui/TrustScore";
import { useDevices } from "@/hooks/useDevices";
import { getDeviceIcon, formatTimestamp, formatMac } from "@/lib/utils";
import type { Device } from "@/lib/types";

type DeviceType = string;
type SortKey = "trust_score_asc" | "trust_score_desc" | "name" | "last_seen";

export default function DevicesPage() {
  const { data: devices, isLoading } = useDevices();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<DeviceType | "all">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "online" | "offline">("all");
  const [sortBy, setSortBy] = useState<SortKey>("trust_score_asc");

  const deviceTypes = useMemo(() => {
    if (!devices) return [];
    return [...new Set(devices.map((d) => d.device_type))];
  }, [devices]);

  const filteredDevices = useMemo(() => {
    if (!devices) return [];

    let filtered = [...devices];

    // Search filter
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.name?.toLowerCase().includes(q) ||
          d.mac?.toLowerCase().includes(q) ||
          d.ip?.toLowerCase().includes(q)
      );
    }

    // Type filter
    if (typeFilter !== "all") {
      filtered = filtered.filter((d) => d.device_type === typeFilter);
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((d) =>
        statusFilter === "online" ? d.online : !d.online
      );
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "trust_score_asc":
          return a.trust_score - b.trust_score;
        case "trust_score_desc":
          return b.trust_score - a.trust_score;
        case "name":
          return (a.name || "").localeCompare(b.name || "");
        case "last_seen":
          return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
        default:
          return 0;
      }
    });

    return filtered;
  }, [devices, search, typeFilter, statusFilter, sortBy]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Devices</h1>
        <p className="text-sm text-slate-400 mt-1">
          {devices?.length ?? 0} devices on your network
        </p>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
            />
            <input
              type="text"
              placeholder="Search by name, MAC, or IP..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-400/50"
            />
          </div>

          {/* Type filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-sky-400/50"
          >
            <option value="all">All Types</option>
            {deviceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as "all" | "online" | "offline")
            }
            className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-sky-400/50"
          >
            <option value="all">All Status</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortKey)}
            className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-sky-400/50"
          >
            <option value="trust_score_asc">Trust (Low first)</option>
            <option value="trust_score_desc">Trust (High first)</option>
            <option value="name">Name</option>
            <option value="last_seen">Last Seen</option>
          </select>
        </div>
      </Card>

      {/* Device List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 skeleton rounded-xl" />
          ))}
        </div>
      ) : filteredDevices.length === 0 ? (
        <Card>
          <p className="text-center text-slate-500 py-8">
            {search || typeFilter !== "all" || statusFilter !== "all"
              ? "No devices match your filters"
              : "No devices found"}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDevices.map((device) => (
            <DeviceCard key={device.id} device={device} />
          ))}
        </div>
      )}
    </div>
  );
}

function DeviceCard({ device }: { device: Device }) {
  const router = useRouter();

  return (
    <div
      className="bg-slate-800/80 border border-slate-700/50 rounded-xl p-4 hover:border-sky-400/30 transition-colors cursor-pointer"
      onClick={() => router.push(`/devices/${device.id}`)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{getDeviceIcon(device.device_type)}</span>
          <div>
            <p className="text-sm font-medium text-slate-200">{device.name}</p>
            <p className="text-xs text-slate-500">
              {device.device_type}
            </p>
          </div>
        </div>
        <Badge variant={device.online ? "success" : "danger"}>
          {device.online ? "Online" : "Offline"}
        </Badge>
      </div>

      <TrustScore score={device.trust_score} size="sm" />

      <div className="mt-3 space-y-1">
        <p className="text-xs text-slate-500 font-mono">
          {formatMac(device.mac)}
        </p>
        <p className="text-xs text-slate-500">
          Last seen: {formatTimestamp(device.last_seen)}
        </p>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-700/30">
        <Link
          href={`/devices/${device.id}`}
          className="text-xs text-sky-400 hover:text-sky-300"
          onClick={(e) => e.stopPropagation()}
        >
          View Details →
        </Link>
      </div>
    </div>
  );
}

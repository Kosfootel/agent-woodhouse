"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2, Pencil, X, Check } from "lucide-react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import TrustScore from "@/components/ui/TrustScore";
import { useDevice, useMarkAsTrusted, useEvents } from "@/hooks/useDevices";
import { getDeviceIcon, formatTimestamp, formatMac } from "@/lib/utils";

export default function DeviceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const deviceId = params.id as string;
  const { data: device, isLoading } = useDevice(deviceId);
  const { data: events } = useEvents();
  const markAsTrusted = useMarkAsTrusted();
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");

  const deviceEvents = events?.filter((e) => e.device_id === deviceId).slice(-20);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 skeleton rounded-lg" />
        <div className="h-40 skeleton rounded-xl" />
        <div className="h-60 skeleton rounded-xl" />
      </div>
    );
  }

  if (!device) {
    return (
      <Card>
        <p className="text-center text-slate-500 py-8">Device not found</p>
      </Card>
    );
  }

  const handleMarkTrusted = () => {
    markAsTrusted.mutate(device);
  };

  const handleEditName = () => {
    if (editing) {
      // In a real app, we'd persist this to the API
      setEditing(false);
    } else {
      setEditName(device.name);
      setEditing(true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/devices")}
          className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold text-slate-100">Device Details</h1>
      </div>

      {/* Device Header */}
      <Card>
        <div className="flex flex-col sm:flex-row items-start gap-4">
          <span className="text-4xl">{getDeviceIcon(device.device_type)}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              {editing ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="text-xl font-bold bg-slate-700/50 border border-slate-600/50 rounded-lg px-2 py-1 text-slate-200 focus:outline-none focus:border-sky-400/50"
                    autoFocus
                  />
                  <button
                    onClick={handleEditName}
                    className="p-1 text-emerald-400 hover:text-emerald-300"
                  >
                    <Check size={18} />
                  </button>
                  <button
                    onClick={() => setEditing(false)}
                    className="p-1 text-slate-500 hover:text-slate-300"
                  >
                    <X size={18} />
                  </button>
                </div>
              ) : (
                <>
                  <h2 className="text-xl font-bold text-slate-100">
                    {device.name}
                  </h2>
                  <button
                    onClick={handleEditName}
                    className="p-1 text-slate-500 hover:text-slate-300"
                  >
                    <Pencil size={14} />
                  </button>
                </>
              )}
              <Badge
                variant={device.online ? "success" : "danger"}
              >
                {device.online ? "Online" : "Offline"}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-4 mt-2 text-sm text-slate-400">
              <span className="font-mono">{formatMac(device.mac)}</span>
              <span>{device.ip}</span>
              {device.first_seen && (
                <span>First seen: {formatTimestamp(device.first_seen)}</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Trust Score + Classification */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Trust Score
          </h3>
          <TrustScore score={device.trust_score} size="lg" />
          <div className="mt-4">
            <Button
              variant="primary"
              onClick={handleMarkTrusted}
              disabled={markAsTrusted.isPending}
            >
              <CheckCircle2 size={16} />
              {markAsTrusted.isPending ? "Marking..." : "Mark as Trusted"}
            </Button>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Classification
          </h3>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-500">Device Type</p>
              <p className="text-lg font-medium text-slate-200">
                {device.device_type}
              </p>
            </div>
            {device.confidence !== undefined && (
              <div>
                <p className="text-xs text-slate-500">Confidence</p>
                <p className="text-lg font-medium text-slate-200 font-mono">
                  {Math.round(device.confidence * 100)}%
                </p>
              </div>
            )}
            {device.behavior && (
              <>
                <div>
                  <p className="text-xs text-slate-500">Normal Hours</p>
                  <p className="text-lg font-medium text-slate-200">
                    {device.behavior.normal_hours}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Normal Connections</p>
                  <p className="text-lg font-medium text-slate-200 font-mono">
                    {device.behavior.normal_connections} devices
                  </p>
                </div>
              </>
            )}
          </div>
        </Card>
      </div>

      {/* Event History */}
      <Card>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Event History
        </h3>
        {deviceEvents && deviceEvents.length > 0 ? (
          <div className="space-y-1">
            {deviceEvents.map((event) => (
              <div
                key={event.id}
                className="flex items-start gap-3 py-2 border-b border-slate-700/30 last:border-0"
              >
                <div className="w-2 h-2 mt-1.5 rounded-full bg-slate-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200">
                    {event.description || event.event_type}
                  </p>
                </div>
                <span className="text-xs text-slate-500 flex-shrink-0">
                  {formatTimestamp(event.timestamp)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No events recorded for this device</p>
        )}
      </Card>
    </div>
  );
}

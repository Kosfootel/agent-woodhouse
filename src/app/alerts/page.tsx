"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, AlertTriangle, Info } from "lucide-react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { useAlerts } from "@/hooks/useDevices";
import { formatTimestamp } from "@/lib/utils";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const { data: alerts, isLoading } = useAlerts();
  const [showAll, setShowAll] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [acknowledged, setAcknowledged] = useState<Set<string>>(new Set());

  const filteredAlerts = useMemo(() => {
    if (!alerts) return [];

    let filtered = [...alerts];

    // Show unacknowledged only by default
    if (!showAll) {
      filtered = filtered.filter((a) => !a.acknowledged && !acknowledged.has(a.id));
    }

    // Severity filter
    if (severityFilter !== "all") {
      filtered = filtered.filter((a) => a.severity === severityFilter);
    }

    // Sort newest first
    filtered.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return filtered;
  }, [alerts, showAll, severityFilter, acknowledged]);

  const handleAcknowledge = (alert: Alert) => {
    setAcknowledged((prev) => new Set([...prev, alert.id]));
  };

  const handleAcknowledgeAll = () => {
    if (alerts) {
      setAcknowledged(new Set(alerts.map((a) => a.id)));
    }
  };

  const severityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <AlertTriangle size={16} className="text-rose-500" />;
      case "warning":
        return <AlertTriangle size={16} className="text-amber-400" />;
      default:
        return <Info size={16} className="text-sky-400" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Alerts</h1>
          <p className="text-sm text-slate-400 mt-1">
            Security events requiring attention
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={handleAcknowledgeAll}>
          <CheckCircle2 size={16} />
          Acknowledge All
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-sky-400/50"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>

        <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={showAll}
            onChange={(e) => setShowAll(e.target.checked)}
            className="rounded border-slate-600 bg-slate-700 text-sky-400 focus:ring-sky-400/50"
          />
          Show acknowledged
        </label>

        {severityFilter !== "all" && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSeverityFilter("all")}
          >
            Clear filter
          </Button>
        )}
      </div>

      {/* Alert List */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 skeleton rounded-xl" />
          ))}
        </div>
      ) : filteredAlerts.length === 0 ? (
        <Card>
          <div className="text-center py-8">
            <CheckCircle2 size={40} className="mx-auto text-emerald-400 mb-3" />
            <p className="text-slate-200 font-medium">
              {severityFilter !== "all"
                ? "No alerts match this filter"
                : "All clear! No alerts to show"}
            </p>
            <p className="text-sm text-slate-500 mt-1">
              {severityFilter !== "all"
                ? "Try changing your filter"
                : "Your network is looking healthy"}
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={() => handleAcknowledge(alert)}
              severityIcon={severityIcon(alert.severity)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function AlertCard({
  alert,
  onAcknowledge,
  severityIcon,
}: {
  alert: Alert;
  onAcknowledge: () => void;
  severityIcon: React.ReactNode;
}) {
  const router = useRouter();

  return (
    <div
      className={`bg-slate-800/80 border-l-4 rounded-xl p-4 ${
        alert.severity === "critical"
          ? "border-l-rose-500"
          : alert.severity === "warning"
          ? "border-l-amber-400"
          : "border-l-sky-400"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{severityIcon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant={
                alert.severity === "critical"
                  ? "danger"
                  : alert.severity === "warning"
                  ? "warning"
                  : "info"
              }
            >
              {alert.severity}
            </Badge>
            <span className="text-xs text-slate-500">
              {formatTimestamp(alert.timestamp)}
            </span>
          </div>
          <p className="text-sm font-medium text-slate-200">{alert.title}</p>
          <p className="text-sm text-slate-400 mt-0.5">{alert.description}</p>
          <div className="flex items-center gap-3 mt-2">
            {alert.device_id && (
              <button
                onClick={() => router.push(`/devices/${alert.device_id}`)}
                className="text-xs text-sky-400 hover:text-sky-300"
              >
                View device →
              </button>
            )}
            <button
              onClick={onAcknowledge}
              className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
            >
              <CheckCircle2 size={12} />
              Acknowledge
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

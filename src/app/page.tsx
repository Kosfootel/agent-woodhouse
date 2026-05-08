"use client";

import { useRouter } from "next/navigation";
import {
  Shield,
  Monitor,
  Bell,
  Activity,
  AlertTriangle,
  Info,
  Eye,
} from "lucide-react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import StatCard from "@/components/ui/StatCard";
import TrendIndicator from "@/components/ui/TrendIndicator";
import { useNetworkSummary, useEvents } from "@/hooks/useDevices";
import { formatTimestamp } from "@/lib/utils";

export default function OverviewPage() {
  const router = useRouter();
  const { data: summary, isLoading: summaryLoading } = useNetworkSummary();
  const { data: events, isLoading: eventsLoading } = useEvents();

  const recentEvents = events?.slice(-5).reverse();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Overview</h1>
        <p className="text-sm text-slate-400 mt-1">
          Real-time network security at a glance
        </p>
      </div>

      {/* Top Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 skeleton rounded-xl" />
            ))}
          </>
        ) : (
          <>
            <StatCard
              label="Network Trust"
              value={
                summary ? `${Math.round(summary.trust_score * 100)}%` : "—"
              }
              icon={<Shield size={20} />}
              subtext={
                summary ? (
                  <TrendIndicator direction={summary.trust_trend} />
                ) : undefined
              }
            />
            <StatCard
              label="Devices"
              value={summary?.total_devices ?? "—"}
              subtext={`${summary?.new_today ?? 0} new today · ${
                summary?.offline ?? 0
              } offline`}
              icon={<Monitor size={20} />}
            />
            <StatCard
              label="Critical Alerts"
              value={summary?.alerts_critical ?? 0}
              subtext={
                summary
                  ? `${summary.alerts_warning} warnings · ${summary.alerts_info} info`
                  : undefined
              }
              icon={<Bell size={20} />}
            />
            <StatCard
              label="Recent Events"
              value={events?.length ?? 0}
              subtext="Last 24 hours"
              icon={<Activity size={20} />}
            />
          </>
        )}
      </div>

      {/* Alert Summary Card */}
      <Card>
        <h2 className="text-lg font-semibold text-slate-100 mb-4">
          Alert Summary (Last 24h)
        </h2>
        {summaryLoading ? (
          <div className="h-16 skeleton rounded-lg" />
        ) : (
          <div className="flex flex-wrap gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-rose-500/20 flex items-center justify-center">
                <AlertTriangle size={20} className="text-rose-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-rose-500 font-mono">
                  {summary?.alerts_critical ?? 0}
                </p>
                <p className="text-xs text-slate-500 uppercase">Critical</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-400/20 flex items-center justify-center">
                <AlertTriangle size={20} className="text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-amber-400 font-mono">
                  {summary?.alerts_warning ?? 0}
                </p>
                <p className="text-xs text-slate-500 uppercase">Warning</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-sky-400/20 flex items-center justify-center">
                <Info size={20} className="text-sky-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-sky-400 font-mono">
                  {summary?.alerts_info ?? 0}
                </p>
                <p className="text-xs text-slate-500 uppercase">Info</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Recent Activity + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Recent Activity
          </h2>
          {eventsLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-10 skeleton rounded-lg" />
              ))}
            </div>
          ) : recentEvents && recentEvents.length > 0 ? (
            <div className="space-y-1">
              {recentEvents.map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-3 py-2.5 border-b border-slate-700/30 last:border-0"
                >
                  <div className="w-2 h-2 mt-2 rounded-full bg-sky-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 truncate">
                      {event.description || event.event_type}
                    </p>
                    {event.device_name && (
                      <p className="text-xs text-slate-500">{event.device_name}</p>
                    )}
                  </div>
                  <span className="text-xs text-slate-500 flex-shrink-0">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No recent activity</p>
          )}
        </Card>

        {/* Quick Actions */}
        <Card>
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <Button
              variant="primary"
              className="w-full justify-center"
              onClick={() => router.push("/alerts")}
            >
              <Eye size={16} />
              Review Alerts
            </Button>
            <Button
              variant="secondary"
              className="w-full justify-center"
              onClick={() => router.push("/devices")}
            >
              <Monitor size={16} />
              View Devices
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-center"
              onClick={() => router.push("/analytics")}
            >
              <Activity size={16} />
              View Analytics
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import Card from "@/components/ui/Card";
import {
  useTrustTrend,
  useDeviceTypeBreakdown,
  useAlertVolume,
  useTopTalkers,
} from "@/hooks/useDevices";
import { formatMac } from "@/lib/utils";


const COLORS = ["#38bdf8", "#34d399", "#fbbf24", "#f43f5e", "#a78bfa", "#fb923c"];

export default function AnalyticsPage() {
  const [trendDays, setTrendDays] = useState(7);
  const { data: trustTrend, isLoading: trendLoading } = useTrustTrend(trendDays);
  const { data: deviceTypes, isLoading: typesLoading } = useDeviceTypeBreakdown();
  const { data: alertVolume, isLoading: volumeLoading } = useAlertVolume();
  const { data: topTalkers, isLoading: talkersLoading } = useTopTalkers();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Analytics</h1>
        <p className="text-sm text-slate-400 mt-1">
          Network trust and activity insights
        </p>
      </div>

      {/* Trust Trend */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-100">
            Network Trust Trend
          </h2>
          <div className="flex gap-2">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTrendDays(days)}
                className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${
                  trendDays === days
                    ? "bg-sky-400/20 text-sky-400 border border-sky-400/30"
                    : "bg-slate-700/50 text-slate-400 hover:text-slate-200 border border-slate-600/50"
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>
        {trendLoading ? (
          <div className="h-64 skeleton rounded-lg" />
        ) : trustTrend && trustTrend.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trustTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  tickFormatter={(val) => {
                    const d = new Date(val);
                    return `${d.getMonth() + 1}/${d.getDate()}`;
                  }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  tickFormatter={(val) => `${Math.round(val * 100)}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    color: "#f1f5f9",
                  }}
                  formatter={(value: unknown) => {
                    const num = Number(value);
                    return [`${Math.round(num * 100)}%`, "Trust Score"];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  dot={{ fill: "#38bdf8", r: 3 }}
                  activeDot={{ r: 5, fill: "#38bdf8" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-sm text-slate-500 text-center py-16">
            Insufficient data to show trust trend
          </p>
        )}
      </Card>

      {/* Device Type Breakdown + Alert Volume */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Type Breakdown */}
        <Card>
          <h2 className="text-lg font-semibold text-slate-100 mb-6">
            Device Type Breakdown
          </h2>
          {typesLoading ? (
            <div className="h-64 skeleton rounded-lg" />
          ) : deviceTypes && deviceTypes.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={deviceTypes}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="count"
                    nameKey="type"
                    labelLine={{ stroke: "#475569" }}
                  >
                    {deviceTypes.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#f1f5f9",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-16">
              No device data available
            </p>
          )}
        </Card>

        {/* Alert Volume */}
        <Card>
          <h2 className="text-lg font-semibold text-slate-100 mb-6">
            Alert Volume Over Time
          </h2>
          {volumeLoading ? (
            <div className="h-64 skeleton rounded-lg" />
          ) : alertVolume && alertVolume.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={alertVolume}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    tickFormatter={(val) => {
                      const d = new Date(val);
                      return `${d.getMonth() + 1}/${d.getDate()}`;
                    }}
                  />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#f1f5f9",
                    }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }}
                  />
                  <Bar
                    dataKey="critical"
                    stackId="a"
                    fill="#f43f5e"
                    name="Critical"
                  />
                  <Bar
                    dataKey="warning"
                    stackId="a"
                    fill="#fbbf24"
                    name="Warning"
                  />
                  <Bar
                    dataKey="info"
                    stackId="a"
                    fill="#38bdf8"
                    name="Info"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-16">
              No alert data available
            </p>
          )}
        </Card>
      </div>

      {/* Top Talkers */}
      <Card>
        <h2 className="text-lg font-semibold text-slate-100 mb-6">
          Top Talkers (Most Active Devices)
        </h2>
        {talkersLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 skeleton rounded-lg" />
            ))}
          </div>
        ) : topTalkers && topTalkers.length > 0 ? (
          <div className="space-y-1">
            {topTalkers.map((talker, index) => (
              <div
                key={talker.device_id}
                className="flex items-center gap-4 py-2.5 border-b border-slate-700/30 last:border-0"
              >
                <span className="text-sm text-slate-500 font-mono w-6 text-right">
                  #{index + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200">{talker.device_name}</p>
                  {talker.mac && (
                    <p className="text-xs text-slate-500 font-mono">
                      {formatMac(talker.mac)}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-sky-400 font-mono">
                    {talker.events}
                  </p>
                  <p className="text-xs text-slate-500">events</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500 text-center py-8">
            No traffic data available
          </p>
        )}
      </Card>
    </div>
  );
}

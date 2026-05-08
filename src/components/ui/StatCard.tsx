"use client";

import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: React.ReactNode;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "stable";
  className?: string;
}

export default function StatCard({
  label,
  value,
  subtext,
  icon,
  className,
}: StatCardProps) {
  return (
    <div className={cn("bg-slate-800/80 border border-slate-700/50 rounded-xl p-4", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{label}</p>
          <p className="text-2xl font-bold text-slate-100 font-mono">{value}</p>
          {subtext && (
            <div className="text-xs text-slate-400 mt-1">{subtext}</div>
          )}
        </div>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
    </div>
  );
}

"use client";

interface TrendIndicatorProps {
  direction: "up" | "down" | "stable";
}

export default function TrendIndicator({ direction }: TrendIndicatorProps) {
  const arrow = direction === "up" ? "↑" : direction === "down" ? "↓" : "→";
  const color =
    direction === "up"
      ? "text-emerald-400"
      : direction === "down"
      ? "text-rose-500"
      : "text-slate-400";

  const label =
    direction === "up" ? "Improving" : direction === "down" ? "Declining" : "Stable";

  return (
    <span className={`inline-flex items-center gap-1 text-sm ${color}`}>
      <span className="text-lg">{arrow}</span>
      {label}
    </span>
  );
}

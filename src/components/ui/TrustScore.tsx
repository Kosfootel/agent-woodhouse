"use client";

import { getTrustColor, getTrustColorClass } from "@/lib/utils";

interface TrustScoreProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showBar?: boolean;
  showLabel?: boolean;
}

export default function TrustScore({
  score,
  size = "md",
  showBar = true,
  showLabel = true,
}: TrustScoreProps) {
  const percentage = Math.round(score * 100);
  const color = getTrustColor(score);
  const colorClass = getTrustColorClass(score);

  const sizeClasses = {
    sm: "text-lg",
    md: "text-2xl",
    lg: "text-4xl",
  };

  const barHeight = {
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
  };

  const label = score >= 0.7 ? "High" : score >= 0.3 ? "Medium" : "Low";

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline gap-2">
        <span className={`font-mono font-bold ${sizeClasses[size]} ${colorClass}`}>
          {percentage}%
        </span>
        {showLabel && (
          <span className="text-xs text-slate-500 uppercase tracking-wider">
            {label}
          </span>
        )}
      </div>
      {showBar && (
        <div className={`w-full ${barHeight[size]} bg-slate-700 rounded-full overflow-hidden`}>
          <div
            className={`${barHeight[size]} rounded-full transition-all duration-500`}
            style={{
              width: `${percentage}%`,
              backgroundColor: color,
            }}
          />
        </div>
      )}
    </div>
  );
}

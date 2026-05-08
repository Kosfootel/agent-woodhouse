"use client";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}

export default function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  const variants = {
    default: "bg-slate-700/50 text-slate-300 border-slate-600/50",
    success: "bg-emerald-400/10 text-emerald-400 border-emerald-400/30",
    warning: "bg-amber-400/10 text-amber-400 border-amber-400/30",
    danger: "bg-rose-500/10 text-rose-500 border-rose-500/30",
    info: "bg-sky-400/10 text-sky-400 border-sky-400/30",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

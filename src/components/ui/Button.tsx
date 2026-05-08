"use client";

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  className?: string;
}

export default function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled = false,
  className = "",
}: ButtonProps) {
  const variants = {
    primary: "bg-sky-400 text-sky-900 hover:bg-sky-300 disabled:bg-sky-400/50",
    secondary: "bg-slate-700 text-slate-200 hover:bg-slate-600 disabled:bg-slate-700/50",
    ghost: "bg-transparent text-slate-300 hover:bg-slate-700/50 disabled:text-slate-500",
    danger: "bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 disabled:bg-rose-500/10",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 rounded-lg font-medium transition-colors ${
        variants[variant]
      } ${sizes[size]} ${disabled ? "cursor-not-allowed" : "cursor-pointer"} ${className}`}
    >
      {children}
    </button>
  );
}

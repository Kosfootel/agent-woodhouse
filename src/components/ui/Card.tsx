"use client";

import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export default function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={cn(
        "bg-slate-800/80 border border-slate-700/50 rounded-xl p-4 md:p-6",
        onClick && "cursor-pointer hover:border-sky-400/30 transition-colors",
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

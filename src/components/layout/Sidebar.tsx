"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Monitor, Bell, BarChart3 } from "lucide-react";

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/devices", label: "Devices", icon: Monitor },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="hidden md:flex md:flex-col w-64 bg-slate-900 border-r border-slate-700/50 h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-slate-700/50">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sky-400/20 flex items-center justify-center">
            <span className="text-sky-400 font-bold text-sm">V</span>
          </div>
          <span className="text-xl font-bold text-slate-100 tracking-tight font-sans">
            Vigil
          </span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-sky-400/10 text-sky-400 border border-sky-400/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700/50">
        <p className="text-xs text-slate-600">Vigil Home Security</p>
        <p className="text-xs text-slate-600">v1.0.0</p>
      </div>
    </aside>
  );
}

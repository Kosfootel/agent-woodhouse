export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const hours = Math.floor(diff / 3600000);

  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMac(mac: string): string {
  if (mac.length === 12 || mac.length === 17) {
    return mac
      .replace(/[^a-fA-F0-9]/g, "")
      .toUpperCase()
      .replace(/(.{2})/g, "$1:")
      .slice(0, 17);
  }
  return mac;
}

export function getTrustColor(score: number): string {
  if (score >= 0.7) return "#34d399";
  if (score >= 0.3) return "#fbbf24";
  return "#f43f5e";
}

export function getTrustColorClass(score: number): string {
  if (score >= 0.7) return "text-emerald-400";
  if (score >= 0.3) return "text-amber-400";
  return "text-rose-500";
}

export function getTrustBarColor(score: number): string {
  if (score >= 0.7) return "bg-emerald-400";
  if (score >= 0.3) return "bg-amber-400";
  return "bg-rose-500";
}

export function getDeviceIcon(type: string): string {
  switch (type.toLowerCase()) {
    case "camera":
      return "📷";
    case "phone":
    case "smartphone":
      return "📱";
    case "computer":
    case "laptop":
    case "desktop":
      return "💻";
    case "iot":
    case "smart device":
      return "🏠";
    default:
      return "❓";
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-rose-500";
    case "warning":
      return "text-amber-400";
    default:
      return "text-sky-400";
  }
}

export function getSeverityBadgeClass(severity: string): string {
  switch (severity) {
    case "critical":
      return "bg-rose-500/20 text-rose-500 border-rose-500/30";
    case "warning":
      return "bg-amber-400/20 text-amber-400 border-amber-400/30";
    default:
      return "bg-sky-400/20 text-sky-400 border-sky-400/30";
  }
}

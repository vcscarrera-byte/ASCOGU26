export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "0";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export function relativeTime(isoDate: string): string {
  try {
    const dt = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - dt.getTime();
    const minutes = Math.floor(diffMs / 60000);
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    if (days === 1) return "ontem";
    return `${days}d`;
  } catch {
    return isoDate?.slice(0, 16) || "";
  }
}

export function sessionBadgeColor(sessionType: string): string {
  const map: Record<string, string> = {
    "Oral Abstract Session": "bg-clinical-oral text-white",
    "Rapid Oral Abstract Session": "bg-clinical-rapidoral text-white",
    "General Session": "bg-clinical-general text-white",
    "Poster Walks": "bg-clinical-tumor text-white",
    "Poster Session": "bg-clinical-poster text-white",
    "Trials in Progress Poster Session": "bg-clinical-poster text-white",
  };
  return map[sessionType] || "bg-gray-200 text-gray-700";
}

export function sessionBadgeLabel(sessionType: string): string {
  const map: Record<string, string> = {
    "Oral Abstract Session": "Oral",
    "Rapid Oral Abstract Session": "Rapid Oral",
    "General Session": "General",
    "Poster Walks": "Poster Walk",
    "Poster Session": "Poster",
    "Trials in Progress Poster Session": "TIP",
    "Networking Event": "Networking",
  };
  return map[sessionType] || sessionType;
}

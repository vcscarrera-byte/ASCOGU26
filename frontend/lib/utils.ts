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

/**
 * Deduplicate tweets that are RTs of the same content.
 * Groups identical RT text together, keeping the one with highest engagement
 * and attaching a list of other users who retweeted.
 */
export interface DeduplicatedTweet {
  tweet: import("@/lib/types").Tweet;
  retweetedBy: string[];
  retweetCount: number;
}

export function deduplicateRTs(tweets: import("@/lib/types").Tweet[]): DeduplicatedTweet[] {
  const groups = new Map<string, import("@/lib/types").Tweet[]>();
  const originals: import("@/lib/types").Tweet[] = [];

  for (const tw of tweets) {
    if (tw.text.startsWith("RT @")) {
      // Normalize RT text to group duplicates
      const key = tw.text.trim();
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(tw);
    } else {
      originals.push(tw);
    }
  }

  const result: DeduplicatedTweet[] = [];

  // Add original tweets (no dedup needed)
  for (const tw of originals) {
    result.push({ tweet: tw, retweetedBy: [], retweetCount: 0 });
  }

  // Add deduplicated RTs (one per unique text, with retweetedBy list)
  for (const [, group] of groups) {
    // Sort by engagement to pick the "best" one
    group.sort((a, b) => (b.total_engagement || 0) - (a.total_engagement || 0));
    const best = group[0];
    const others = group.slice(1).map((t) => t.username);
    result.push({
      tweet: best,
      retweetedBy: others,
      retweetCount: group.length,
    });
  }

  // Sort by relevance score descending
  result.sort((a, b) => (b.tweet.relevance_score || 0) - (a.tweet.relevance_score || 0));

  return result;
}

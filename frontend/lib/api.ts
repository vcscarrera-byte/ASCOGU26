const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }
  const res = await fetch(url.toString(), { next: { revalidate: 120 } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getStats: () => fetchAPI<import("./types").Stats>("/api/stats"),
  getDates: () => fetchAPI<{ dates: string[] }>("/api/dates"),
  getFilters: () => fetchAPI<import("./types").FilterOptions>("/api/filters"),

  getTopTweets: (params?: { limit?: number; tumors?: string; drugs?: string }) =>
    fetchAPI<{ tweets: import("./types").Tweet[]; total: number }>("/api/tweets/top", params),

  getTweets: (params?: { page?: number; size?: number; search?: string; sort?: string; tumors?: string; drugs?: string; curated?: boolean }) =>
    fetchAPI<{ tweets: import("./types").Tweet[]; total: number; page: number; total_pages: number }>("/api/tweets", params),

  getTweetAbstracts: (tweetId: string) =>
    fetchAPI<{ abstracts: import("./types").Abstract[] }>(`/api/tweets/${tweetId}/abstracts`),

  getAuthors: (params?: { limit?: number; tumors?: string; drugs?: string; curated?: boolean }) =>
    fetchAPI<{ authors: import("./types").Author[]; total: number }>("/api/authors", params),

  getAbstracts: (params?: { page?: number; size?: number; tumors?: string; drugs?: string; sessions?: string; search?: string; sort?: string }) =>
    fetchAPI<{ abstracts: import("./types").Abstract[]; total: number }>("/api/abstracts", params),

  getAbstractDetail: (id: string) =>
    fetchAPI<{ abstract: import("./types").Abstract; linked_tweets: import("./types").Tweet[] }>(`/api/abstracts/${id}`),

  getAbstractStats: () =>
    fetchAPI<{ total: number; by_session_type: Record<string, number>; by_tumor: Record<string, number>; with_buzz: number }>("/api/abstracts/stats"),

  getBuzzAbstracts: (limit?: number) =>
    fetchAPI<{ abstracts: import("./types").Abstract[] }>("/api/abstracts/buzz", { limit }),

  getVolume: (params?: { tumors?: string; drugs?: string }) =>
    fetchAPI<{ data: import("./types").VolumeDay[] }>("/api/metrics/volume", params),

  getBrief: (date: string, lang?: string) =>
    fetchAPI<{ brief: string | null; date: string }>(`/api/briefs/${date}`, { lang: lang || "pt" }),
};

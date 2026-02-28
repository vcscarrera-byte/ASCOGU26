import type { Stats, Tweet, Abstract, Author, VolumeDay, FilterOptions, AbstractDetail, Briefs, KolSummaries } from "./types";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json();
}

// --------------- helpers for client-side filtering ---------------

function matchSearch(text: string, query: string): boolean {
  return text.toLowerCase().includes(query.toLowerCase());
}

function sortTweets(tweets: Tweet[], sort: string): Tweet[] {
  const sorted = [...tweets];
  switch (sort) {
    case "relevance":
      return sorted.sort((a, b) => (b.relevance_score ?? 0) - (a.relevance_score ?? 0));
    case "engagement":
      return sorted.sort(
        (a, b) =>
          (b.like_count + b.retweet_count + b.reply_count + b.quote_count) -
          (a.like_count + a.retweet_count + a.reply_count + a.quote_count)
      );
    case "recent":
      return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    default:
      return sorted;
  }
}

function filterTweets(
  tweets: Tweet[],
  opts: { search?: string; tumors?: string; drugs?: string; curated?: boolean }
): Tweet[] {
  let result = tweets;
  if (opts.search) {
    const q = opts.search;
    result = result.filter((t) => matchSearch(t.text, q) || matchSearch(t.name, q) || matchSearch(t.username, q));
  }
  if (opts.tumors) {
    const tumorList = opts.tumors.split(",").map((s) => s.trim().toLowerCase());
    result = result.filter((t) =>
      t.clinical_tags?.tumor_types?.some((tt) => tumorList.includes(tt.toLowerCase()))
    );
  }
  if (opts.drugs) {
    const drugList = opts.drugs.split(",").map((s) => s.trim().toLowerCase());
    result = result.filter((t) =>
      t.clinical_tags?.drugs?.some((d) => drugList.includes(d.toLowerCase()))
    );
  }
  if (opts.curated) {
    result = result.filter((t) => t.is_curated === 1);
  }
  return result;
}

// --------------- public API (same shape the pages expect) ---------------

export const api = {
  getStats: () => fetchJSON<Stats>("/data/stats.json"),

  getDates: async (): Promise<string[]> => {
    return fetchJSON<string[]>("/data/dates.json");
  },

  getFilters: () => fetchJSON<FilterOptions>("/data/filters.json"),

  getTopTweets: async (params?: { limit?: number; tumors?: string; drugs?: string }): Promise<Tweet[]> => {
    let tweets = await fetchJSON<Tweet[]>("/data/tweets_top.json");
    if (params?.tumors || params?.drugs) {
      tweets = filterTweets(tweets, { tumors: params.tumors, drugs: params.drugs });
    }
    const limit = params?.limit ?? 15;
    return tweets.slice(0, limit);
  },

  getTweets: async (params?: {
    page?: number;
    size?: number;
    search?: string;
    sort?: string;
    tumors?: string;
    drugs?: string;
    curated?: boolean;
  }): Promise<{ tweets: Tweet[]; total: number; page: number; total_pages: number }> => {
    let tweets = await fetchJSON<Tweet[]>("/data/tweets_all.json");
    tweets = filterTweets(tweets, {
      search: params?.search,
      tumors: params?.tumors,
      drugs: params?.drugs,
      curated: params?.curated,
    });
    tweets = sortTweets(tweets, params?.sort ?? "relevance");
    const page = params?.page ?? 1;
    const size = params?.size ?? 20;
    const total = tweets.length;
    const total_pages = Math.max(1, Math.ceil(total / size));
    const start = (page - 1) * size;
    return { tweets: tweets.slice(start, start + size), total, page, total_pages };
  },

  getAuthors: async (params?: {
    limit?: number;
    tumors?: string;
    drugs?: string;
    curated?: boolean;
  }): Promise<Author[]> => {
    const authors = await fetchJSON<Author[]>("/data/authors.json");
    const limit = params?.limit ?? 50;
    return authors.slice(0, limit);
  },

  getAbstracts: async (params?: {
    page?: number;
    size?: number;
    tumors?: string;
    drugs?: string;
    sessions?: string;
    search?: string;
    sort?: string;
  }): Promise<{ abstracts: Abstract[]; total: number }> => {
    let abstracts = await fetchJSON<Abstract[]>("/data/abstracts_all.json");
    if (params?.search) {
      const q = params.search;
      abstracts = abstracts.filter(
        (a) =>
          matchSearch(a.title, q) ||
          matchSearch(a.abstract_number, q) ||
          matchSearch(a.presenter || "", q) ||
          matchSearch(a.drugs || "", q) ||
          matchSearch(a.tumor_type || "", q) ||
          matchSearch(a.body || "", q)
      );
    }
    if (params?.tumors) {
      const tumorList = params.tumors.split(",").map((s) => s.trim().toLowerCase());
      abstracts = abstracts.filter((a) => tumorList.includes((a.tumor_type || "").toLowerCase()));
    }
    if (params?.drugs) {
      const drugList = params.drugs.split(",").map((s) => s.trim().toLowerCase());
      abstracts = abstracts.filter((a) =>
        drugList.some((d) => (a.drugs || "").toLowerCase().includes(d))
      );
    }
    if (params?.sessions) {
      const sessionList = params.sessions.split(",").map((s) => s.trim().toLowerCase());
      abstracts = abstracts.filter((a) => sessionList.includes((a.session_type || "").toLowerCase()));
    }
    const size = params?.size ?? 50;
    const page = params?.page ?? 1;
    const total = abstracts.length;
    const start = (page - 1) * size;
    return { abstracts: abstracts.slice(start, start + size), total };
  },

  getAbstractDetail: async (id: string): Promise<{ abstract: Abstract; linked_tweets: Tweet[] }> => {
    const details = await fetchJSON<Record<string, AbstractDetail>>("/data/abstracts_detail.json");
    const detail = details[id];
    if (!detail) throw new Error(`Abstract ${id} not found`);
    const { linked_tweets, ...abstractData } = detail;
    return { abstract: abstractData as Abstract, linked_tweets: linked_tweets || [] };
  },

  getAbstractStats: () =>
    fetchJSON<{ total: number; by_session_type: Record<string, number>; by_tumor: Record<string, number>; top_drugs: Record<string, number>; with_buzz: number }>(
      "/data/abstracts_stats.json"
    ),

  getBuzzAbstracts: async (limit?: number): Promise<Abstract[]> => {
    const abstracts = await fetchJSON<Abstract[]>("/data/abstracts_buzz.json");
    return limit ? abstracts.slice(0, limit) : abstracts;
  },

  getDrugMentions: () => fetchJSON<{ drug: string; count: number }[]>("/data/drug_mentions.json"),

  getVolume: async (): Promise<VolumeDay[]> => {
    return fetchJSON<VolumeDay[]>("/data/metrics_volume.json");
  },

  getBrief: async (date: string, lang?: string): Promise<string | null> => {
    const briefs = await fetchJSON<Briefs>("/data/briefs.json");
    const entry = briefs[date];
    if (!entry) return null;
    const language = lang || "pt";
    return entry[language as keyof typeof entry] || null;
  },

  getKolSummaries: () => fetchJSON<KolSummaries>("/data/kol_summaries.json"),

  getTweetsByAuthor: async (username: string): Promise<Tweet[]> => {
    const tweets = await fetchJSON<Tweet[]>("/data/tweets_all.json");
    return tweets.filter((t) => t.username.toLowerCase() === username.toLowerCase());
  },

  getAuthorByUsername: async (username: string): Promise<Author | null> => {
    const authors = await fetchJSON<Author[]>("/data/authors.json");
    return authors.find((a) => a.username.toLowerCase() === username.toLowerCase()) || null;
  },
};

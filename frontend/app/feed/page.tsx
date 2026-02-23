"use client";

import { useEffect, useState, useMemo } from "react";
import { Tweet } from "@/lib/types";
import TweetCard from "@/components/TweetCard";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";
import FilterSidebar, { ActiveFilters } from "@/components/FilterSidebar";

export default function FeedPage() {
  const [allTweets, setAllTweets] = useState<Tweet[]>([]);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("relevance");
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<ActiveFilters>({ tumors: [], drugs: [], sessionTypes: [] });
  const [loading, setLoading] = useState(true);

  const size = 20;

  // Fetch all tweets once
  useEffect(() => {
    async function load() {
      try {
        const tweets = await fetch("/data/tweets_all.json").then((r) => r.json());
        setAllTweets(tweets);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Client-side filter, sort, paginate
  const { tweets, total, totalPages } = useMemo(() => {
    let filtered = allTweets;

    // Text search
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.text.toLowerCase().includes(q) ||
          t.name.toLowerCase().includes(q) ||
          t.username.toLowerCase().includes(q)
      );
    }

    // Clinical filters
    if (filters.tumors.length > 0) {
      filtered = filtered.filter((t) => {
        const tags = t.clinical_tags?.tumor_types || [];
        return filters.tumors.some((f) => tags.includes(f));
      });
    }
    if (filters.drugs.length > 0) {
      filtered = filtered.filter((t) => {
        const tags = t.clinical_tags?.drugs || [];
        return filters.drugs.some((f) => tags.includes(f));
      });
    }

    // Sort
    const sorted = [...filtered];
    switch (sort) {
      case "relevance":
        sorted.sort((a, b) => (b.relevance_score ?? 0) - (a.relevance_score ?? 0));
        break;
      case "engagement":
        sorted.sort(
          (a, b) =>
            (b.like_count + b.retweet_count + b.reply_count + b.quote_count) -
            (a.like_count + a.retweet_count + a.reply_count + a.quote_count)
        );
        break;
      case "recent":
        sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
    }

    const total = sorted.length;
    const totalPages = Math.max(1, Math.ceil(total / size));
    const start = (page - 1) * size;
    return { tweets: sorted.slice(start, start + size), total, totalPages };
  }, [allTweets, search, sort, page, filters]);

  // Reset page when search, sort, or filters change
  useEffect(() => {
    setPage(1);
  }, [search, sort, filters]);

  const sortOptions = [
    { value: "relevance", label: "Relevancia" },
    { value: "engagement", label: "Engagement" },
    { value: "recent", label: "Recentes" },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-6">📰 Principais postagens</h1>

      {/* Clinical Filters */}
      <FilterSidebar onFilterChange={setFilters} />

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <input
          type="text"
          placeholder="Buscar tweets..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-64"
        />
        <div className="flex border border-slate-200 rounded-lg overflow-hidden">
          {sortOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSort(opt.value)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                sort === opt.value
                  ? "bg-primary text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <span className="text-sm text-slate-500 ml-auto">
          {total.toLocaleString()} tweets
        </span>
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-xl p-5 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-1/3 mb-3" />
              <div className="h-3 bg-slate-200 rounded w-full mb-2" />
              <div className="h-3 bg-slate-200 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : tweets.length > 0 ? (
        <div className="space-y-4">
          {tweets.map((t, i) => (
            <TweetCard
              key={t.tweet_id}
              tweet={t}
              rank={sort !== "recent" ? (page - 1) * size + i + 1 : undefined}
              showRelevance={sort === "relevance"}
            />
          ))}
        </div>
      ) : (
        <EmptyState icon="🔍" title="Nenhum tweet encontrado" subtitle="Tente outro termo de busca ou ajuste os filtros." />
      )}

      <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}

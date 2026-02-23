"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Tweet } from "@/lib/types";
import TweetCard from "@/components/TweetCard";
import Pagination from "@/components/Pagination";
import EmptyState from "@/components/EmptyState";

export default function FeedPage() {
  const [tweets, setTweets] = useState<Tweet[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("relevance");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const size = 20;

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await api.getTweets({ page, size, sort, search: search || undefined });
        setTweets(res.tweets);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [page, sort, search]);

  const sortOptions = [
    { value: "relevance", label: "Relevancia" },
    { value: "engagement", label: "Engagement" },
    { value: "recent", label: "Recentes" },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-6">{"\uD83D\uDCF0"} Principais postagens</h1>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <input
          type="text"
          placeholder="Buscar tweets..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-64"
        />
        <div className="flex border border-slate-200 rounded-lg overflow-hidden">
          {sortOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { setSort(opt.value); setPage(1); }}
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
        <EmptyState icon={"\uD83D\uDD0D"} title="Nenhum tweet encontrado" subtitle="Tente outro termo de busca." />
      )}

      <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Stats, Tweet, Abstract } from "@/lib/types";
import MetricCard from "@/components/MetricCard";
import TweetCard from "@/components/TweetCard";
import AbstractCard from "@/components/AbstractCard";
import EmptyState from "@/components/EmptyState";

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [topTweets, setTopTweets] = useState<Tweet[]>([]);
  const [buzzAbstracts, setBuzzAbstracts] = useState<Abstract[]>([]);
  const [brief, setBrief] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"posts" | "abstracts" | "brief">("posts");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, t, a, dates] = await Promise.all([
          api.getStats(),
          api.getTopTweets({ limit: 15 }),
          api.getBuzzAbstracts(10),
          api.getDates(),
        ]);
        setStats(s);
        setTopTweets(t);
        setBuzzAbstracts(a);

        if (dates.length > 0) {
          const latestDate = dates[dates.length - 1];
          const b = await api.getBrief(latestDate, "pt");
          setBrief(b);
        }
      } catch (err) {
        console.error("Failed to load:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-400 text-lg">Carregando dados...</div>
      </div>
    );
  }

  const tabs = [
    { key: "posts" as const, label: "\uD83D\uDD25 Destaques do Dia" },
    { key: "abstracts" as const, label: "\uD83D\uDCC4 Abstracts em Alta" },
    { key: "brief" as const, label: "\uD83D\uDCDD Resumo IA" },
  ];

  return (
    <div>
      {/* Hero */}
      <div className="mb-8">
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight">
          {"\uD83D\uDCE1"} ASCO GU RADAR
        </h1>
        <div className="text-sm font-semibold text-primary uppercase tracking-widest mt-1">2026</div>
        <p className="text-lg text-slate-500 mt-2 max-w-2xl">
          Destaques dos KOLs de uro-oncologia no ASCO GU 2026, ranqueados por relevancia clinica.
        </p>
      </div>

      {/* Metrics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard icon={"\uD83D\uDCE1"} label="Tweets" value={stats.total_tweets} />
          <MetricCard icon={"\uD83D\uDC64"} label="Autores" value={stats.unique_authors} />
          <MetricCard icon="\u2B50" label="KOLs Ativos" value={stats.curated_active} />
          <MetricCard icon={"\uD83D\uDD2C"} label="Abstracts" value={stats.abstract_count} />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "posts" && (
        <div className="space-y-4">
          {topTweets.length > 0 ? (
            topTweets.map((t, i) => (
              <TweetCard key={t.tweet_id} tweet={t} rank={i + 1} showRelevance />
            ))
          ) : (
            <EmptyState icon={"\uD83D\uDCED"} title="Nenhum tweet encontrado" />
          )}
        </div>
      )}

      {activeTab === "abstracts" && (
        <div className="space-y-4">
          {buzzAbstracts.length > 0 ? (
            <>
              <p className="text-sm text-slate-500 mb-2">Abstracts mais discutidos nos tweets</p>
              {buzzAbstracts.map((a, i) => (
                <AbstractCard key={a.abstract_number} abstract={a} rank={i + 1} />
              ))}
            </>
          ) : (
            <EmptyState icon={"\uD83D\uDD2C"} title="Nenhum abstract com buzz" />
          )}
        </div>
      )}

      {activeTab === "brief" && (
        <div>
          {brief ? (
            <div className="prose prose-slate max-w-none bg-white border border-slate-200 rounded-xl p-6 shadow-sm" dangerouslySetInnerHTML={{ __html: brief.replace(/\n/g, "<br/>") }} />
          ) : (
            <EmptyState icon={"\uD83D\uDCDD"} title="Nenhum brief disponivel" subtitle="O resumo IA sera gerado apos a coleta de dados." />
          )}
        </div>
      )}
    </div>
  );
}

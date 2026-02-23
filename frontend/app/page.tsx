"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
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
  const [briefPt, setBriefPt] = useState<string | null>(null);
  const [briefEn, setBriefEn] = useState<string | null>(null);
  const [briefLang, setBriefLang] = useState<"pt" | "en">("pt");
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
          const [bPt, bEn] = await Promise.all([
            api.getBrief(latestDate, "pt"),
            api.getBrief(latestDate, "en"),
          ]);
          setBriefPt(bPt);
          setBriefEn(bEn);
        }
      } catch (err) {
        console.error("Failed to load:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const currentBrief = briefLang === "pt" ? briefPt : briefEn;

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
          <MetricCard icon="📡" label="Tweets" value={stats.total_tweets} />
          <MetricCard icon="👥" label="Autores" value={stats.unique_authors} />
          <MetricCard icon="⭐" label="KOLs Ativos" value={stats.curated_active} />
          <MetricCard icon="🔬" label="Abstracts" value={stats.abstract_count} />
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
          {/* Language selector */}
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-slate-500 font-medium">Idioma:</span>
            <div className="inline-flex rounded-lg border border-slate-200 overflow-hidden">
              <button
                onClick={() => setBriefLang("pt")}
                className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                  briefLang === "pt"
                    ? "bg-primary text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                PT-BR
              </button>
              <button
                onClick={() => setBriefLang("en")}
                className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                  briefLang === "en"
                    ? "bg-primary text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                EN
              </button>
            </div>
          </div>

          {currentBrief ? (
            <article className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-sm prose prose-slate max-w-none prose-headings:text-slate-900 prose-h1:text-2xl prose-h1:font-bold prose-h1:border-b prose-h1:border-slate-200 prose-h1:pb-3 prose-h2:text-xl prose-h2:font-semibold prose-h2:mt-8 prose-h2:mb-3 prose-h2:text-primary-dark prose-strong:text-slate-800 prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-li:marker:text-primary">
              <ReactMarkdown>{currentBrief}</ReactMarkdown>
            </article>
          ) : (
            <EmptyState icon="📝" title="Nenhum brief disponivel" subtitle="O resumo IA sera gerado apos a coleta de dados." />
          )}
        </div>
      )}
    </div>
  );
}

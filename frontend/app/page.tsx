"use client";

import { useEffect, useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import Link from "next/link";
import { api } from "@/lib/api";
import { Stats, Tweet, Abstract } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
import { deduplicateRTs } from "@/lib/utils";
import MetricCard from "@/components/MetricCard";
import TweetCard from "@/components/TweetCard";
import AbstractCard from "@/components/AbstractCard";
import EmptyState from "@/components/EmptyState";
import FilterSidebar, { ActiveFilters } from "@/components/FilterSidebar";

export default function Home() {
  const { lang, t } = useI18n();

  const [stats, setStats] = useState<Stats | null>(null);
  const [allTopTweets, setAllTopTweets] = useState<Tweet[]>([]);
  const [buzzAbstracts, setBuzzAbstracts] = useState<Abstract[]>([]);
  const [briefPt, setBriefPt] = useState<string | null>(null);
  const [briefEn, setBriefEn] = useState<string | null>(null);
  const [dates, setDates] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<"day" | "congress" | "abstracts" | "brief">("day");
  const [loading, setLoading] = useState(true);
  const [showMethodology, setShowMethodology] = useState(false);

  // Highlight filters
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<ActiveFilters>({ tumors: [], drugs: [], sessionTypes: [] });
  const [selectedDate, setSelectedDate] = useState<string>("");

  useEffect(() => {
    async function load() {
      try {
        const [s, tweets, a, d] = await Promise.all([
          api.getStats(),
          api.getTopTweets({ limit: 50 }),
          api.getBuzzAbstracts(10),
          api.getDates(),
        ]);
        setStats(s);
        setAllTopTweets(tweets);
        setBuzzAbstracts(a);
        setDates(d);
        if (d.length > 0) {
          setSelectedDate(d[d.length - 1]);
          const [bPt, bEn] = await Promise.all([
            api.getBrief(d[d.length - 1], "pt"),
            api.getBrief(d[d.length - 1], "en"),
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

  // Filter and deduplicate tweets for "day" tab
  const dayDeduped = useMemo(() => {
    let filtered = allTopTweets.filter((tw) => {
      const tweetDate = tw.created_at?.slice(0, 10);
      return tweetDate === selectedDate;
    });
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (tw) =>
          tw.text.toLowerCase().includes(q) ||
          tw.name.toLowerCase().includes(q) ||
          tw.username.toLowerCase().includes(q)
      );
    }
    if (filters.tumors.length > 0) {
      filtered = filtered.filter((tw) => {
        const tags = tw.clinical_tags?.tumor_types || [];
        return filters.tumors.some((f) => tags.includes(f));
      });
    }
    if (filters.drugs.length > 0) {
      filtered = filtered.filter((tw) => {
        const tags = tw.clinical_tags?.drugs || [];
        return filters.drugs.some((f) => tags.includes(f));
      });
    }
    return deduplicateRTs(filtered);
  }, [allTopTweets, selectedDate, search, filters]);

  // Filter and deduplicate tweets for "congress" tab (all dates)
  const congressDeduped = useMemo(() => {
    let filtered = allTopTweets;
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (tw) =>
          tw.text.toLowerCase().includes(q) ||
          tw.name.toLowerCase().includes(q) ||
          tw.username.toLowerCase().includes(q)
      );
    }
    if (filters.tumors.length > 0) {
      filtered = filtered.filter((tw) => {
        const tags = tw.clinical_tags?.tumor_types || [];
        return filters.tumors.some((f) => tags.includes(f));
      });
    }
    if (filters.drugs.length > 0) {
      filtered = filtered.filter((tw) => {
        const tags = tw.clinical_tags?.drugs || [];
        return filters.drugs.some((f) => tags.includes(f));
      });
    }
    return deduplicateRTs(filtered).slice(0, 20);
  }, [allTopTweets, search, filters]);

  const currentBrief = lang === "pt" ? briefPt : briefEn;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-pulse text-slate-400 text-lg">
          {t("Carregando dados...", "Loading data...")}
        </div>
      </div>
    );
  }

  const tabs = [
    { key: "day" as const, label: t("🔥 Destaques do Dia", "🔥 Today's Highlights") },
    { key: "congress" as const, label: t("🏆 Destaques do Congresso", "🏆 Congress Highlights") },
    { key: "abstracts" as const, label: t("📄 Abstracts em Alta", "📄 Trending Abstracts") },
    { key: "brief" as const, label: t("📝 Resumo IA", "📝 AI Summary") },
  ];

  const formatDate = (d: string) => {
    const [y, m, day] = d.split("-");
    return lang === "pt" ? `${day}/${m}/${y}` : `${m}/${day}/${y}`;
  };

  return (
    <div>
      {/* Hero */}
      <div className="mb-8">
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight">
          📡 ASCO GU RADAR
        </h1>
        <div className="text-sm font-semibold text-primary uppercase tracking-widest mt-1">2026</div>
        <p className="text-lg text-slate-500 mt-2 max-w-2xl">
          {t(
            "Destaques dos líderes de opinião em uro-oncologia no ASCO GU 2026, ranqueados por relevância clínica.",
            "Highlights from key opinion leaders in uro-oncology at ASCO GU 2026, ranked by clinical relevance."
          )}
        </p>

        {/* How it works toggle */}
        <button
          onClick={() => setShowMethodology(!showMethodology)}
          className="mt-2 text-sm text-primary hover:text-primary-dark font-medium flex items-center gap-1 py-2 min-h-[44px]"
        >
          {t("ℹ️ Como funciona este radar?", "ℹ️ How does this radar work?")}
          <svg className={`w-3.5 h-3.5 transition-transform ${showMethodology ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {showMethodology && (
          <div className="mt-3 bg-white border border-slate-200 rounded-xl p-4 sm:p-5 text-sm text-slate-600 space-y-2 max-w-3xl">
            <p className="font-semibold text-slate-800">
              {t("📋 Metodologia de coleta", "📋 Collection methodology")}
            </p>
            <p>
              {t(
                "O ASCO GU RADAR monitora duas fontes de dados no Twitter/X:",
                "ASCO GU RADAR monitors two data sources on Twitter/X:"
              )}
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong>{t("Hashtags:", "Hashtags:")}</strong>{" "}
                {t(
                  "Todos os tweets com #ASCOGU26, #ASCOGU2026 ou #ASCOGU",
                  "All tweets with #ASCOGU26, #ASCOGU2026 or #ASCOGU"
                )}
              </li>
              <li>
                <strong>{t("Líderes de Opinião:", "Key Opinion Leaders:")}</strong>{" "}
                {t(
                  "58 especialistas curados em uro-oncologia (Brasil, EUA, Europa) — seus tweets são capturados quando mencionam temas de câncer geniturinário.",
                  "58 curated uro-oncology specialists (Brazil, USA, Europe) — their tweets are captured when they mention genitourinary cancer topics."
                )}
                {" "}
                <Link href="/autores" className="text-primary hover:underline font-medium">
                  {t("Ver lista completa →", "View full list →")}
                </Link>
              </li>
            </ul>
            <p>
              <strong>{t("Ranking:", "Ranking:")}</strong>{" "}
              {t(
                "Os destaques são ranqueados por um score de relevância (0-100) que considera: engagement (40pts), status de líder de opinião (20pts), tags clínicas (20pts), discussão gerada (10pts) e penalidade de RT (-30pts).",
                "Highlights are ranked by a relevance score (0-100) that considers: engagement (40pts), KOL status (20pts), clinical tags (20pts), discussion generated (10pts), and RT penalty (-30pts)."
              )}
            </p>
          </div>
        )}
      </div>

      {/* Metrics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard icon="📡" label={t("Tweets", "Tweets")} value={stats.total_tweets} />
          <MetricCard icon="👥" label={t("Autores", "Authors")} value={stats.unique_authors} />
          <Link href="/autores" className="block">
            <MetricCard
              icon="⭐"
              label={t("Líderes de Opinião", "Opinion Leaders")}
              value={stats.curated_active}
            />
          </Link>
          <MetricCard icon="🔬" label="Abstracts" value={stats.abstract_count} />
        </div>
      )}

      {/* Search + Filters for highlights */}
      {(activeTab === "day" || activeTab === "congress") && (
        <div className="mb-4 space-y-3">
          <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3">
            <input
              type="text"
              placeholder={t("Buscar por médico, droga ou estudo...", "Search by physician, drug or study...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full sm:w-72 px-4 py-3 sm:py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
            <div className="flex items-center gap-3">
              {activeTab === "day" && dates.length > 0 && (
                <select
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="px-3 py-3 sm:py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  {dates.map((d) => (
                    <option key={d} value={d}>
                      {formatDate(d)}
                    </option>
                  ))}
                </select>
              )}
              <span className="text-sm text-slate-400 whitespace-nowrap">
                {activeTab === "day"
                  ? `${dayDeduped.length} ${t("posts", "posts")}`
                  : `${congressDeduped.length} ${t("posts", "posts")}`}
              </span>
            </div>
          </div>
          <FilterSidebar onFilterChange={setFilters} />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6 -mx-4 sm:mx-0">
        <div className="flex gap-0 overflow-x-auto px-4 sm:px-0 scrollbar-hide">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 sm:px-4 py-3 sm:py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap min-h-[44px] ${
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

      {/* Tab: Day highlights */}
      {activeTab === "day" && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-700">
            {t(`Destaques de ${formatDate(selectedDate)}`, `Highlights from ${formatDate(selectedDate)}`)}
          </h2>
          {dayDeduped.length > 0 ? (
            dayDeduped.map((item, i) => (
              <div key={item.tweet.tweet_id}>
                <TweetCard tweet={item.tweet} rank={i + 1} showRelevance />
                {item.retweetCount > 1 && (
                  <div className="ml-4 mt-1 text-xs text-slate-400 flex items-center gap-1">
                    🔁 {t(
                      `Retweetado por ${item.retweetCount} pessoas`,
                      `Retweeted by ${item.retweetCount} people`
                    )}
                    {item.retweetedBy.length > 0 && (
                      <span className="text-slate-300">
                        ({item.retweetedBy.slice(0, 5).map(u => `@${u}`).join(", ")}
                        {item.retweetedBy.length > 5 && ` +${item.retweetedBy.length - 5}`})
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : (
            <EmptyState
              icon="📭"
              title={t("Nenhum destaque para esta data", "No highlights for this date")}
              subtitle={t("Tente outra data ou ajuste os filtros.", "Try another date or adjust the filters.")}
            />
          )}
        </div>
      )}

      {/* Tab: Congress highlights (all dates) */}
      {activeTab === "congress" && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-700">
            {t("Top 20 — Todos os dias", "Top 20 — All dates")}
          </h2>
          {congressDeduped.length > 0 ? (
            congressDeduped.map((item, i) => (
              <div key={item.tweet.tweet_id}>
                <TweetCard tweet={item.tweet} rank={i + 1} showRelevance />
                {item.retweetCount > 1 && (
                  <div className="ml-4 mt-1 text-xs text-slate-400 flex items-center gap-1">
                    🔁 {t(
                      `Retweetado por ${item.retweetCount} pessoas`,
                      `Retweeted by ${item.retweetCount} people`
                    )}
                    {item.retweetedBy.length > 0 && (
                      <span className="text-slate-300">
                        ({item.retweetedBy.slice(0, 5).map(u => `@${u}`).join(", ")}
                        {item.retweetedBy.length > 5 && ` +${item.retweetedBy.length - 5}`})
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : (
            <EmptyState
              icon="📭"
              title={t("Nenhum destaque encontrado", "No highlights found")}
              subtitle={t("Ajuste os filtros de busca.", "Adjust search filters.")}
            />
          )}
        </div>
      )}

      {/* Tab: Abstracts */}
      {activeTab === "abstracts" && (
        <div className="space-y-4">
          {buzzAbstracts.length > 0 ? (
            <>
              <p className="text-sm text-slate-500 mb-2">
                {t("Abstracts mais discutidos nos tweets", "Most discussed abstracts in tweets")}
              </p>
              {buzzAbstracts.map((a, i) => (
                <AbstractCard key={a.abstract_number} abstract={a} rank={i + 1} />
              ))}
            </>
          ) : (
            <EmptyState icon="🔬" title={t("Nenhum abstract com discussão", "No abstracts with discussion")} />
          )}
        </div>
      )}

      {/* Tab: Brief */}
      {activeTab === "brief" && (
        <div>
          {currentBrief ? (
            <article className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-sm prose prose-slate max-w-none prose-headings:text-slate-900 prose-h1:text-2xl prose-h1:font-bold prose-h1:border-b prose-h1:border-slate-200 prose-h1:pb-3 prose-h2:text-xl prose-h2:font-semibold prose-h2:mt-8 prose-h2:mb-3 prose-h2:text-primary-dark prose-strong:text-slate-800 prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-li:marker:text-primary">
              <ReactMarkdown>{currentBrief}</ReactMarkdown>
            </article>
          ) : (
            <EmptyState
              icon="📝"
              title={t("Nenhum resumo disponível", "No summary available")}
              subtitle={t("O resumo IA será gerado após a coleta de dados.", "The AI summary will be generated after data collection.")}
            />
          )}
        </div>
      )}
    </div>
  );
}

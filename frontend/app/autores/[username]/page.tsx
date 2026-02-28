"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { api } from "@/lib/api";
import { Author, Tweet, KolSummaries } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
import { formatNumber } from "@/lib/utils";
import TweetCard from "@/components/TweetCard";
import EmptyState from "@/components/EmptyState";

export default function KolProfilePage() {
  const params = useParams();
  const username = params.username as string;
  const { lang, t } = useI18n();

  const [author, setAuthor] = useState<Author | null>(null);
  const [tweets, setTweets] = useState<Tweet[]>([]);
  const [kolSummaries, setKolSummaries] = useState<KolSummaries>({});
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string>("");

  useEffect(() => {
    async function load() {
      try {
        const [a, tw, summaries] = await Promise.all([
          api.getAuthorByUsername(username),
          api.getTweetsByAuthor(username),
          api.getKolSummaries(),
        ]);
        setAuthor(a);
        setTweets(tw);
        setKolSummaries(summaries);

        // Set default selected date to most recent
        const tweetDates = [...new Set(tw.map((t) => t.created_at?.slice(0, 10)).filter(Boolean))].sort();
        if (tweetDates.length > 0) {
          setSelectedDate(tweetDates[tweetDates.length - 1]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [username]);

  // Available dates (from tweets)
  const availableDates = useMemo(() => {
    const dates = [...new Set(tweets.map((t) => t.created_at?.slice(0, 10)).filter(Boolean))].sort();
    return dates;
  }, [tweets]);

  // Tweets for selected date
  const dateTweets = useMemo(() => {
    if (!selectedDate) return tweets;
    return tweets.filter((t) => t.created_at?.slice(0, 10) === selectedDate);
  }, [tweets, selectedDate]);

  // Images for selected date
  const dateImages = useMemo(() => {
    return dateTweets
      .filter((t) => t.media && t.media.length > 0)
      .flatMap((t) =>
        (t.media || []).map((m) => ({
          ...m,
          tweetId: t.tweet_id,
          username: t.username,
        }))
      );
  }, [dateTweets]);

  // KOL summary for selected date
  const summary = useMemo(() => {
    const kolData = kolSummaries[username.toLowerCase()] || kolSummaries[username];
    if (!kolData || !selectedDate) return null;
    const dateData = kolData[selectedDate];
    if (!dateData) return null;
    return lang === "pt" ? dateData.pt : dateData.en;
  }, [kolSummaries, username, selectedDate, lang]);

  const formatDate = (d: string) => {
    const [y, m, day] = d.split("-");
    return lang === "pt" ? `${day}/${m}/${y}` : `${m}/${day}/${y}`;
  };

  if (loading) {
    return (
      <div className="animate-pulse text-slate-400 py-20 text-center text-lg">
        {t("Carregando perfil...", "Loading profile...")}
      </div>
    );
  }

  if (!author) {
    return (
      <div className="py-10">
        <Link href="/autores" className="text-primary hover:underline font-medium mb-6 inline-block">
          &larr; {t("Voltar para autores", "Back to authors")}
        </Link>
        <EmptyState
          icon="👤"
          title={t("Autor não encontrado", "Author not found")}
          subtitle={t(`Não encontramos o perfil de @${username}.`, `We couldn't find the profile for @${username}.`)}
        />
      </div>
    );
  }

  const totalDateEngagement = dateTweets.reduce((sum, t) => sum + t.total_engagement, 0);

  return (
    <div>
      {/* Back button */}
      <Link href="/autores" className="text-primary hover:underline font-medium mb-6 inline-block min-h-[44px] flex items-center">
        &larr; {t("Voltar para autores", "Back to authors")}
      </Link>

      {/* Profile header */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 sm:p-6 shadow-sm mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">{author.name}</h1>
              {author.is_curated === 1 && (
                <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2 py-0.5 rounded uppercase tracking-wide">
                  KOL
                </span>
              )}
            </div>
            <div className="text-sm text-slate-500 mb-2">
              @{author.username} &middot; {author.followers_count?.toLocaleString()} {t("seguidores", "followers")}
            </div>
            {author.description && (
              <p className="text-sm text-slate-600 leading-relaxed">{author.description}</p>
            )}
          </div>

          {/* Stats */}
          <div className="flex gap-4 sm:gap-6 shrink-0">
            <div className="text-center">
              <div className="text-xl font-bold text-slate-900">{author.tweet_count}</div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wide">Tweets</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-slate-900">{formatNumber(author.total_engagement)}</div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wide">Engagement</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-slate-900">{Math.round(author.avg_engagement)}</div>
              <div className="text-[11px] text-slate-500 uppercase tracking-wide">Eng/Tweet</div>
            </div>
          </div>
        </div>
      </div>

      {/* Date selector */}
      {availableDates.length > 0 && (
        <div className="flex items-center gap-3 mb-6 flex-wrap">
          <span className="text-sm font-medium text-slate-600">{t("Data:", "Date:")}</span>
          <div className="flex gap-2 flex-wrap">
            {availableDates.map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDate(d)}
                className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors min-h-[36px] ${
                  selectedDate === d
                    ? "bg-primary text-white"
                    : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {formatDate(d)}
              </button>
            ))}
          </div>
          <span className="text-sm text-slate-400 ml-auto">
            {dateTweets.length} tweets &middot; {formatNumber(totalDateEngagement)} engagement
          </span>
        </div>
      )}

      {/* AI Summary */}
      {summary && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-700 mb-3 flex items-center gap-2">
            📝 {t("Resumo IA", "AI Summary")}
          </h2>
          <article className="bg-white border border-slate-200 rounded-xl p-5 sm:p-6 shadow-sm prose prose-slate max-w-none prose-sm prose-a:text-primary prose-a:no-underline hover:prose-a:underline">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </article>
        </div>
      )}

      {/* Image gallery */}
      {dateImages.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-700 mb-3 flex items-center gap-2">
            🖼️ {t("Imagens", "Images")} ({dateImages.length})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {dateImages.map((img) => {
              const imgSrc = img.local_url || img.url || img.preview_image_url;
              if (!imgSrc) return null;
              return (
                <a
                  key={img.media_key}
                  href={`https://x.com/${img.username}/status/${img.tweetId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <img
                    src={imgSrc}
                    alt={img.alt_text || "Tweet image"}
                    className="rounded-lg w-full h-40 object-cover border border-slate-200 hover:opacity-90 transition-opacity"
                    loading="lazy"
                  />
                </a>
              );
            })}
          </div>
        </div>
      )}

      {/* Tweets */}
      <div>
        <h2 className="text-lg font-semibold text-slate-700 mb-3 flex items-center gap-2">
          📡 Tweets {selectedDate && `(${formatDate(selectedDate)})`}
        </h2>
        {dateTweets.length > 0 ? (
          <div className="space-y-3">
            {dateTweets.map((tw) => (
              <TweetCard key={tw.tweet_id} tweet={tw} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon="📭"
            title={t("Nenhum tweet nesta data", "No tweets on this date")}
            subtitle={t("Selecione outra data.", "Select another date.")}
          />
        )}
      </div>
    </div>
  );
}

import Link from "next/link";
import { Tweet } from "@/lib/types";
import { formatNumber, relativeTime } from "@/lib/utils";
import Badge from "./Badge";

interface TweetCardProps {
  tweet: Tweet;
  rank?: number;
  compact?: boolean;
  showRelevance?: boolean;
}

export default function TweetCard({ tweet, rank, compact, showRelevance }: TweetCardProps) {
  const tweetUrl = `https://x.com/${tweet.username}/status/${tweet.tweet_id}`;
  const isRT = tweet.text.startsWith("RT @");

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:border-slate-300">
      {/* Header */}
      <div className="flex items-start sm:items-center gap-2 text-sm text-slate-600 mb-3 flex-wrap">
        {rank && <span className="font-bold text-primary text-base">#{rank}</span>}
        <Link href={`/autores/${tweet.username}`} className="font-semibold text-slate-900 break-all hover:text-primary transition-colors">
          {tweet.name}
        </Link>
        <Link href={`/autores/${tweet.username}`} className="text-slate-400 break-all hover:text-primary transition-colors">
          @{tweet.username}
        </Link>
        {tweet.is_curated === 1 && <span title="KOL Curado">&#11088;</span>}
        {tweet.verified === 1 && <span title="Verificado" className="text-blue-500">&#10003;</span>}
        <span className="hidden sm:inline text-slate-400">&middot;</span>
        <span className="text-slate-400 text-xs sm:text-sm">{relativeTime(tweet.created_at)}</span>
      </div>

      {/* Badges */}
      {tweet.clinical_tags && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {showRelevance && tweet.relevance_score != null && (
            <Badge label={String(Math.round(tweet.relevance_score))} variant={tweet.relevance_score >= 60 ? "relevance" : "gray"} />
          )}
          {tweet.clinical_tags.tumor_types?.map((t) => (
            <Badge key={t} label={t} variant="tumor" />
          ))}
          {tweet.clinical_tags.drugs?.map((d) => (
            <Badge key={d} label={d} variant="drug" />
          ))}
        </div>
      )}

      {/* Text */}
      <p className={`text-sm sm:text-base leading-relaxed text-slate-800 mb-3 break-words ${isRT ? "italic" : ""}`}>
        {tweet.text}
      </p>

      {/* Media */}
      {tweet.media && tweet.media.length > 0 && (
        <div className={`mb-3 grid gap-2 ${tweet.media.length === 1 ? "grid-cols-1" : "grid-cols-2"}`}>
          {tweet.media.map((m) => {
            const imgSrc = m.local_url || m.url || m.preview_image_url;
            if (!imgSrc) return null;
            return (
              <a key={m.media_key} href={imgSrc} target="_blank" rel="noopener noreferrer">
                <img
                  src={imgSrc}
                  alt={m.alt_text || "Tweet image"}
                  className="rounded-lg w-full object-cover max-h-72 border border-slate-200"
                  loading="lazy"
                />
              </a>
            );
          })}
        </div>
      )}

      {/* Metrics */}
      <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-xs sm:text-sm text-slate-500">
        <span title="Likes">&#10084;&#65039; {formatNumber(tweet.like_count)}</span>
        <span title="Retweets">&#128257; {formatNumber(tweet.retweet_count)}</span>
        <span title="Respostas">&#128172; {formatNumber(tweet.reply_count)}</span>
        {!compact && (
          <>
            <span className="hidden sm:inline" title="Impressoes">&#128065; {formatNumber(tweet.impression_count)}</span>
            <span className="hidden sm:inline" title="Favoritos">&#128278; {formatNumber(tweet.bookmark_count)}</span>
          </>
        )}
        <a
          href={tweetUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto text-primary hover:text-primary-dark font-medium hover:underline transition-colors py-1 min-h-[44px] flex items-center"
        >
          Ver no X &rarr;
        </a>
      </div>
    </div>
  );
}

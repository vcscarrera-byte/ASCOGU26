import Link from "next/link";
import { Author } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

interface AuthorCardProps {
  author: Author;
  rank: number;
}

export default function AuthorCard({ author, rank }: AuthorCardProps) {
  return (
    <Link href={`/autores/${author.username}`} className="block">
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:border-slate-300 cursor-pointer">
        <div className="flex items-start sm:items-center gap-3 sm:gap-4">
          {/* Rank */}
          <div className="text-xl sm:text-2xl font-bold text-primary min-w-[36px] sm:min-w-[48px] text-center shrink-0">
            #{rank}
          </div>

          {/* Info + Stats wrapper */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
              {/* Info */}
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-base sm:text-lg font-semibold text-slate-900 break-words">{author.name}</span>
                  {author.is_curated === 1 && (
                    <span className="bg-amber-100 text-amber-800 text-[11px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide shrink-0">
                      KOL
                    </span>
                  )}
                </div>
                <div className="text-sm text-slate-500 mt-0.5 truncate">
                  @{author.username} &middot; {author.followers_count?.toLocaleString()} seguidores
                </div>
              </div>

              {/* Stats */}
              <div className="flex gap-4 sm:gap-6 shrink-0">
                <div className="text-center">
                  <div className="text-lg sm:text-xl font-bold text-slate-900">{author.tweet_count}</div>
                  <div className="text-[10px] sm:text-[11px] text-slate-500 uppercase tracking-wide">Tweets</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-xl font-bold text-slate-900">{formatNumber(author.total_engagement)}</div>
                  <div className="text-[10px] sm:text-[11px] text-slate-500 uppercase tracking-wide">Engagement</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-xl font-bold text-slate-900">{Math.round(author.avg_engagement)}</div>
                  <div className="text-[10px] sm:text-[11px] text-slate-500 uppercase tracking-wide">Eng/Tweet</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}

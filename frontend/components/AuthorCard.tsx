import { Author } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

interface AuthorCardProps {
  author: Author;
  rank: number;
}

export default function AuthorCard({ author, rank }: AuthorCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:border-slate-300 flex items-center gap-4 flex-wrap">
      {/* Rank */}
      <div className="text-2xl font-bold text-primary min-w-[48px] text-center">
        #{rank}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-[200px]">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-slate-900">{author.name}</span>
          {author.is_curated === 1 && (
            <span className="bg-amber-100 text-amber-800 text-[11px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide">
              KOL
            </span>
          )}
        </div>
        <div className="text-sm text-slate-500 mt-0.5">
          @{author.username} &middot; {author.followers_count?.toLocaleString()} seguidores
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-6">
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
  );
}

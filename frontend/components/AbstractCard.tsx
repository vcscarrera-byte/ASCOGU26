import { Abstract } from "@/lib/types";
import { sessionBadgeColor, sessionBadgeLabel } from "@/lib/utils";
import Badge from "./Badge";

interface AbstractCardProps {
  abstract: Abstract;
  rank?: number;
  compact?: boolean;
  onDetailClick?: (abstractNumber: string) => void;
}

export default function AbstractCard({ abstract, rank, compact, onDetailClick }: AbstractCardProps) {
  const genes = abstract.genes?.split("; ").filter(Boolean) || [];
  const drugs = abstract.drugs?.split("; ").filter(Boolean) || [];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:border-slate-300">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm mb-2 flex-wrap">
        {rank && <span className="font-bold text-primary text-base">#{rank}</span>}
        <span className="font-bold text-slate-700">#{abstract.abstract_number}</span>
        {abstract.poster_board_number && (
          <span className="text-slate-500 font-medium">{abstract.poster_board_number}</span>
        )}
        <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold ${sessionBadgeColor(abstract.session_type)}`}>
          {sessionBadgeLabel(abstract.session_type)}
        </span>
        {abstract.linked_tweet_count > 0 && (
          <Badge label={`${abstract.linked_tweet_count} tweets`} variant="buzz" />
        )}
      </div>

      {/* Title */}
      <h3
        className="text-base font-semibold text-slate-900 leading-snug mb-2"
        dangerouslySetInnerHTML={{
          __html: abstract.title.length > 200
            ? abstract.title.slice(0, 200) + "..."
            : abstract.title,
        }}
      />

      {/* Presenter + tumor */}
      {(abstract.presenter || abstract.tumor_type) && (
        <p className="text-sm text-slate-500 mb-2">
          {[abstract.presenter, abstract.tumor_type].filter(Boolean).join(" \u00B7 ")}
        </p>
      )}

      {/* Clinical badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {abstract.tumor_type && <Badge label={abstract.tumor_type} variant="tumor" />}
        {drugs.map((d, i) => <Badge key={`drug-${i}-${d}`} label={d} variant="drug" />)}
        {genes.map((g, i) => <Badge key={`gene-${i}-${g}`} label={g} variant="gene" />)}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {!compact && abstract.url && (
          <a href={abstract.url} target="_blank" rel="noopener noreferrer"
            className="text-sm text-primary hover:text-primary-dark font-medium hover:underline transition-colors py-1 min-h-[44px] flex items-center">
            Ver no ASCO &rarr;
          </a>
        )}
        {onDetailClick && (
          <button
            onClick={() => onDetailClick(abstract.abstract_number)}
            className="text-sm text-slate-500 hover:text-primary font-medium transition-colors py-1 min-h-[44px] flex items-center"
          >
            Ver detalhe
          </button>
        )}
      </div>
    </div>
  );
}

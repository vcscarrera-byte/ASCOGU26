"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { Abstract, Tweet } from "@/lib/types";
import { sessionBadgeColor, sessionBadgeLabel } from "@/lib/utils";
import Badge from "@/components/Badge";
import TweetCard from "@/components/TweetCard";
import EmptyState from "@/components/EmptyState";

interface AbstractDetailData extends Abstract {
  presenter_role?: string;
  date?: string;
  imported_at?: string;
  updated_at?: string;
  linked_tweets: Tweet[];
}

export default function AbstractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { t } = useI18n();
  const id = params.id as string;

  const [detail, setDetail] = useState<AbstractDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/data/abstracts_detail.json");
        const data: Record<string, AbstractDetailData> = await res.json();
        const entry = data[id];
        if (entry) {
          setDetail(entry);
        } else {
          setNotFound(true);
        }
      } catch (err) {
        console.error(err);
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    }
    if (id) load();
  }, [id]);

  if (loading) {
    return (
      <div className="animate-pulse text-slate-400 py-20 text-center text-lg">
        {t("Carregando dados...", "Loading data...")}
      </div>
    );
  }

  if (notFound || !detail) {
    return (
      <div>
        <button
          onClick={() => router.push("/abstracts")}
          className="inline-flex items-center gap-1 text-sm text-primary hover:text-primary-dark font-medium mb-6 transition-colors"
        >
          &larr; {t("Voltar para abstracts", "Back to abstracts")}
        </button>
        <EmptyState
          icon="🔬"
          title={t("Abstract nao encontrado", "Abstract not found")}
          subtitle={t(
            "O abstract solicitado nao foi encontrado.",
            "The requested abstract was not found."
          )}
        />
      </div>
    );
  }

  const genes = detail.genes?.split("; ").filter(Boolean) || [];
  const drugs = detail.drugs?.split("; ").filter(Boolean) || [];
  const subjects = detail.subjects?.split("; ").filter(Boolean) || [];
  const linkedTweets = detail.linked_tweets || [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back link */}
      <button
        onClick={() => router.push("/abstracts")}
        className="inline-flex items-center gap-1 text-sm text-primary hover:text-primary-dark font-medium mb-6 transition-colors"
      >
        &larr; {t("Voltar para abstracts", "Back to abstracts")}
      </button>

      {/* Header card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm mb-6">
        {/* Abstract number + session badge */}
        <div className="flex items-center gap-3 mb-4 flex-wrap">
          <span className="text-2xl font-bold text-primary">
            #{detail.abstract_number}
          </span>
          {detail.poster_board_number && (
            <span className="text-sm font-medium text-slate-500">
              {detail.poster_board_number}
            </span>
          )}
          <span
            className={`inline-block px-2.5 py-0.5 rounded-md text-xs font-semibold ${sessionBadgeColor(
              detail.session_type
            )}`}
          >
            {sessionBadgeLabel(detail.session_type)}
          </span>
        </div>

        {/* Title */}
        <h1
          className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug mb-4"
          dangerouslySetInnerHTML={{ __html: detail.title }}
        />

        {/* Presenter */}
        {detail.presenter && (
          <p className="text-sm text-slate-600 mb-1">
            <strong>{t("Apresentador", "Presenter")}:</strong>{" "}
            {detail.presenter}
            {detail.presenter_role && (
              <span className="text-slate-400 ml-1">
                ({detail.presenter_role})
              </span>
            )}
          </p>
        )}

        {/* Session title */}
        {detail.session_title && (
          <p className="text-sm text-slate-600 mb-4">
            <strong>{t("Sessao", "Session")}:</strong> {detail.session_title}
          </p>
        )}

        {/* Clinical badges */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {detail.tumor_type && (
            <Badge label={detail.tumor_type} variant="tumor" />
          )}
          {drugs.map((d, i) => (
            <Badge key={`drug-${i}-${d}`} label={d} variant="drug" />
          ))}
          {genes.map((g, i) => (
            <Badge key={`gene-${i}-${g}`} label={g} variant="gene" />
          ))}
          {subjects.map((s, i) => (
            <Badge key={`subj-${i}-${s}`} label={s} variant="gray" />
          ))}
        </div>

        {/* External link */}
        {detail.url && (
          <a
            href={detail.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:text-primary-dark font-medium hover:underline transition-colors"
          >
            {t("Ver no ASCO", "View on ASCO")} &rarr;
          </a>
        )}
      </div>

      {/* Body content */}
      {detail.body &&
        !detail.body.toLowerCase().includes("full, final text") && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm mb-6">
            <div
              className="prose prose-slate prose-sm sm:prose-base max-w-none
                prose-b:font-semibold prose-b:text-slate-800
                prose-table:border prose-table:border-slate-200
                prose-td:p-2 prose-td:border prose-td:border-slate-200
                prose-th:p-2 prose-th:border prose-th:border-slate-200 prose-th:bg-slate-50"
              dangerouslySetInnerHTML={{ __html: detail.body }}
            />
          </div>
        )}

      {/* Metadata grid */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          {detail.tumor_type && (
            <div>
              <strong className="text-slate-700">
                {t("Tumor", "Tumor")}:
              </strong>{" "}
              <span className="text-slate-600">{detail.tumor_type}</span>
            </div>
          )}
          {detail.drugs && (
            <div>
              <strong className="text-slate-700">
                {t("Drogas", "Drugs")}:
              </strong>{" "}
              <span className="text-slate-600">{detail.drugs}</span>
            </div>
          )}
          {detail.genes && (
            <div>
              <strong className="text-slate-700">
                {t("Genes", "Genes")}:
              </strong>{" "}
              <span className="text-slate-600">{detail.genes}</span>
            </div>
          )}
          {detail.organizations && (
            <div>
              <strong className="text-slate-700">
                {t("Instituicoes", "Organizations")}:
              </strong>{" "}
              <span className="text-slate-600">{detail.organizations}</span>
            </div>
          )}
          {detail.countries && (
            <div>
              <strong className="text-slate-700">
                {t("Paises", "Countries")}:
              </strong>{" "}
              <span className="text-slate-600">{detail.countries}</span>
            </div>
          )}
          {detail.doi && (
            <div>
              <strong className="text-slate-700">DOI:</strong>{" "}
              <span className="text-slate-600">{detail.doi}</span>
            </div>
          )}
          {detail.subjects && (
            <div className="sm:col-span-2">
              <strong className="text-slate-700">
                {t("Assuntos", "Subjects")}:
              </strong>{" "}
              <span className="text-slate-600">{detail.subjects}</span>
            </div>
          )}
        </div>
      </div>

      {/* Linked tweets */}
      {linkedTweets.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            {linkedTweets.length} {t("tweets linkados", "linked tweets")}
          </h2>
          <div className="space-y-3">
            {linkedTweets.slice(0, 10).map((tw) => (
              <TweetCard key={tw.tweet_id} tweet={tw} compact />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { VolumeDay, Abstract } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import Link from "next/link";

/* ------------------------------------------------------------------ */
/*  Bar Chart (tweets, authors)                                        */
/* ------------------------------------------------------------------ */

function BarChart({
  data,
  getValue,
  maxValue,
  color,
  label,
  formatValue = (v: number) => v.toLocaleString(),
}: {
  data: VolumeDay[];
  getValue: (d: VolumeDay) => number;
  maxValue: number;
  color: string;
  label: string;
  formatValue?: (v: number) => string;
}) {
  const BAR_AREA_HEIGHT = 200;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800 mb-6">{label}</h2>
      <div className="flex items-end gap-1 sm:gap-2" style={{ height: BAR_AREA_HEIGHT + 48 }}>
        {data.map((d) => {
          const value = getValue(d);
          const barHeight = maxValue > 0 ? Math.max(4, (value / maxValue) * BAR_AREA_HEIGHT) : 4;
          const isToday = d.date === new Date().toISOString().slice(0, 10);
          const isMax = value === maxValue;

          return (
            <div
              key={d.date}
              className="flex-1 flex flex-col items-center justify-end group"
              style={{ height: BAR_AREA_HEIGHT + 48 }}
            >
              <div
                className={`text-[10px] sm:text-xs font-semibold mb-1 transition-colors ${
                  isMax ? "text-slate-900" : "text-slate-400 group-hover:text-slate-600"
                }`}
              >
                {formatValue(value)}
              </div>
              <div
                className={`w-full max-w-[48px] rounded-t-md transition-all duration-500 ease-out ${
                  isToday ? "ring-2 ring-offset-1 ring-blue-400" : ""
                }`}
                style={{
                  height: barHeight,
                  background: isMax
                    ? `linear-gradient(to top, ${color}, ${color}dd)`
                    : `linear-gradient(to top, ${color}99, ${color}cc)`,
                  opacity: isToday ? 1 : 0.85,
                }}
              />
              <div
                className={`text-[10px] sm:text-xs mt-2 ${
                  isToday ? "text-blue-600 font-bold" : "text-slate-400"
                }`}
              >
                {d.date.slice(5)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Stacked Bar Chart (engagement)                                     */
/* ------------------------------------------------------------------ */

function StackedBarChart({ data, maxEngagement }: { data: VolumeDay[]; maxEngagement: number }) {
  const BAR_AREA_HEIGHT = 200;
  const segments = [
    { key: "likes" as const, color: "#f87171", label: "Likes" },
    { key: "retweets" as const, color: "#34d399", label: "Retweets" },
    { key: "replies" as const, color: "#60a5fa", label: "Replies" },
    { key: "quotes" as const, color: "#fbbf24", label: "Quotes" },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800 mb-6">Engagement por Dia</h2>
      <div className="flex items-end gap-1 sm:gap-2" style={{ height: BAR_AREA_HEIGHT + 48 }}>
        {data.map((d) => {
          const total = d.engagement;
          const totalHeight = maxEngagement > 0 ? Math.max(4, (total / maxEngagement) * BAR_AREA_HEIGHT) : 4;
          const isToday = d.date === new Date().toISOString().slice(0, 10);
          const isMax = total === maxEngagement;

          return (
            <div
              key={d.date}
              className="flex-1 flex flex-col items-center justify-end group"
              style={{ height: BAR_AREA_HEIGHT + 48 }}
            >
              <div
                className={`text-[10px] sm:text-xs font-semibold mb-1 transition-colors ${
                  isMax ? "text-slate-900" : "text-slate-400 group-hover:text-slate-600"
                }`}
              >
                {total.toLocaleString()}
              </div>
              <div
                className={`w-full max-w-[48px] rounded-t-md overflow-hidden flex flex-col-reverse ${
                  isToday ? "ring-2 ring-offset-1 ring-blue-400" : ""
                }`}
                style={{ height: totalHeight }}
              >
                {segments.map((seg) => {
                  const segValue = d[seg.key];
                  const segHeight = total > 0 ? (segValue / total) * totalHeight : 0;
                  return (
                    <div
                      key={seg.key}
                      style={{ height: segHeight, backgroundColor: seg.color }}
                    />
                  );
                })}
              </div>
              <div
                className={`text-[10px] sm:text-xs mt-2 ${
                  isToday ? "text-blue-600 font-bold" : "text-slate-400"
                }`}
              >
                {d.date.slice(5)}
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-4 mt-4 text-xs text-slate-500">
        {segments.map((seg) => (
          <span key={seg.key} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: seg.color }} />
            {seg.label}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Horizontal Bar Chart (drugs)                                       */
/* ------------------------------------------------------------------ */

function HorizontalBarChart({
  items,
  maxCount,
  color,
  label,
}: {
  items: { name: string; count: number }[];
  maxCount: number;
  color: string;
  label: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">{label}</h2>
      <div className="space-y-2">
        {items.map((item, i) => {
          const width = maxCount > 0 ? Math.max(3, (item.count / maxCount) * 100) : 3;
          return (
            <div key={item.name} className="flex items-center gap-3">
              <div className="w-[140px] sm:w-[180px] text-xs sm:text-sm text-slate-600 truncate text-right shrink-0" title={item.name}>
                {item.name}
              </div>
              <div className="flex-1 h-6 bg-slate-50 rounded-md overflow-hidden">
                <div
                  className="h-full rounded-md transition-all duration-500 flex items-center justify-end pr-2"
                  style={{
                    width: `${width}%`,
                    background: `linear-gradient(to right, ${color}88, ${color})`,
                  }}
                >
                  <span className="text-[10px] font-bold text-white drop-shadow-sm">
                    {item.count}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Top Studies List                                                    */
/* ------------------------------------------------------------------ */

const SESSION_BADGES: Record<string, { label: string; color: string }> = {
  "General Session": { label: "GS", color: "bg-red-100 text-red-700" },
  "Oral Abstract Session": { label: "Oral", color: "bg-amber-100 text-amber-700" },
  "Rapid Oral Abstract Session": { label: "Rapid", color: "bg-blue-100 text-blue-700" },
  "Poster Session": { label: "Poster", color: "bg-slate-100 text-slate-600" },
  "Trials in Progress Poster Session": { label: "TIP", color: "bg-violet-100 text-violet-700" },
};

function TopStudies({ abstracts }: { abstracts: Abstract[] }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Estudos Mais Comentados</h2>
      <div className="space-y-3">
        {abstracts.map((a, i) => {
          const badge = SESSION_BADGES[a.session_type] || { label: a.session_type, color: "bg-slate-100 text-slate-600" };
          return (
            <Link
              key={a.abstract_number}
              href={`/abstracts/${a.abstract_number}`}
              className="block p-3 rounded-lg border border-slate-100 hover:border-blue-200 hover:bg-blue-50/50 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="flex flex-col items-center shrink-0 pt-0.5">
                  <div className="w-8 h-8 rounded-full bg-blue-500 text-white text-sm font-bold flex items-center justify-center">
                    {a.linked_tweet_count}
                  </div>
                  <span className="text-[9px] text-slate-400 mt-0.5">tweets</span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5 mb-1">
                    <span className="text-xs font-mono text-slate-400">#{a.abstract_number}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${badge.color}`}>
                      {badge.label}
                    </span>
                    {a.tumor_type && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                        {a.tumor_type}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-700 line-clamp-2 leading-snug">
                    {a.title.replace(/<[^>]*>/g, "")}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">{a.presenter}</p>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Page                                                          */
/* ------------------------------------------------------------------ */

export default function MetricasPage() {
  const [data, setData] = useState<VolumeDay[]>([]);
  const [buzzAbstracts, setBuzzAbstracts] = useState<Abstract[]>([]);
  const [drugMentions, setDrugMentions] = useState<{ drug: string; count: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [volumeData, buzz, drugs] = await Promise.all([
          api.getVolume(),
          api.getBuzzAbstracts(10),
          api.getDrugMentions(),
        ]);
        setData(volumeData);
        setBuzzAbstracts(buzz);
        setDrugMentions(drugs);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse text-slate-400 py-20 text-center text-lg">
        Carregando metricas...
      </div>
    );
  }

  if (data.length === 0) {
    return <EmptyState icon={"\uD83D\uDCCA"} title="Nenhum dado disponivel" />;
  }

  const maxTweets = Math.max(...data.map((d) => d.tweets));
  const maxEngagement = Math.max(...data.map((d) => d.engagement));
  const maxAuthors = Math.max(...data.map((d) => d.authors));
  const maxDrugCount = drugMentions.length > 0 ? drugMentions[0].count : 1;

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-8">
        {"\uD83D\uDCCA"} Metricas
      </h1>

      <div className="space-y-6">
        {/* Volume charts */}
        <BarChart
          data={data}
          getValue={(d) => d.tweets}
          maxValue={maxTweets}
          color="#3b82f6"
          label="Tweets por Dia"
        />

        <StackedBarChart data={data} maxEngagement={maxEngagement} />

        <BarChart
          data={data}
          getValue={(d) => d.authors}
          maxValue={maxAuthors}
          color="#8b5cf6"
          label="Autores Unicos por Dia"
        />

        {/* Two-column: Top Studies + Top Drugs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {buzzAbstracts.length > 0 && (
            <TopStudies abstracts={buzzAbstracts} />
          )}

          {drugMentions.length > 0 && (
            <HorizontalBarChart
              items={drugMentions.map((d) => ({ name: d.drug, count: d.count }))}
              maxCount={maxDrugCount}
              color="#f59e0b"
              label="Drogas Mais Mencionadas nos Tweets"
            />
          )}
        </div>
      </div>
    </div>
  );
}

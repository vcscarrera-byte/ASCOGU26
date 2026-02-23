"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { VolumeDay } from "@/lib/types";
import EmptyState from "@/components/EmptyState";

export default function MetricasPage() {
  const [data, setData] = useState<VolumeDay[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const volumeData = await api.getVolume();
        setData(volumeData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="animate-pulse text-slate-400 py-20 text-center text-lg">Carregando metricas...</div>;
  }

  if (data.length === 0) {
    return <EmptyState icon={"\uD83D\uDCCA"} title="Nenhum dado disponivel" />;
  }

  const maxTweets = Math.max(...data.map((d) => d.tweets));
  const maxEngagement = Math.max(...data.map((d) => d.engagement));

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-8">{"\uD83D\uDCCA"} Metricas</h1>

      {/* Tweets per day */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Tweets por Dia</h2>
        <div className="flex items-end gap-2 h-48">
          {data.map((d) => (
            <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
              <div className="text-[10px] text-slate-500 font-medium">{d.tweets}</div>
              <div
                className="w-full bg-primary rounded-t-md transition-all duration-300 min-h-[4px]"
                style={{ height: `${Math.max(4, (d.tweets / maxTweets) * 100)}%` }}
              />
              <div className="text-[10px] text-slate-400 mt-1">{d.date.slice(5)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Engagement per day */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Engagement por Dia</h2>
        <div className="flex items-end gap-2 h-48">
          {data.map((d) => (
            <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
              <div className="text-[10px] text-slate-500 font-medium">{d.engagement.toLocaleString()}</div>
              <div className="w-full flex flex-col-reverse rounded-t-md overflow-hidden" style={{ height: `${Math.max(4, (d.engagement / maxEngagement) * 100)}%` }}>
                <div className="bg-red-400" style={{ flex: d.likes }} />
                <div className="bg-emerald-400" style={{ flex: d.retweets }} />
                <div className="bg-blue-400" style={{ flex: d.replies }} />
                <div className="bg-amber-400" style={{ flex: d.quotes }} />
              </div>
              <div className="text-[10px] text-slate-400 mt-1">{d.date.slice(5)}</div>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-3 sm:gap-4 mt-3 text-[11px] text-slate-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-400 rounded-sm" /> Likes</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-emerald-400 rounded-sm" /> Retweets</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-400 rounded-sm" /> Replies</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-amber-400 rounded-sm" /> Quotes</span>
        </div>
      </div>

      {/* Authors per day */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Autores Unicos por Dia</h2>
        <div className="flex items-end gap-2 h-40">
          {data.map((d) => (
            <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
              <div className="text-[10px] text-slate-500 font-medium">{d.authors}</div>
              <div className="w-2 bg-primary rounded-full" style={{ height: `${Math.max(8, (d.authors / Math.max(...data.map((x) => x.authors))) * 100)}%` }} />
              <div className="text-[10px] text-slate-400 mt-1">{d.date.slice(5)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

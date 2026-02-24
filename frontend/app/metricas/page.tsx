"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { VolumeDay } from "@/lib/types";
import EmptyState from "@/components/EmptyState";

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
        {data.map((d, i) => {
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

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-8">
        {"\uD83D\uDCCA"} Metricas
      </h1>

      <div className="space-y-6">
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
      </div>
    </div>
  );
}

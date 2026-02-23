"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Author } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
import AuthorCard from "@/components/AuthorCard";
import EmptyState from "@/components/EmptyState";

export default function AutoresPage() {
  const { t } = useI18n();
  const [authors, setAuthors] = useState<Author[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "curated">("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const authors = await api.getAuthors({ limit: 50 });
        setAuthors(authors);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = authors.filter((a) => {
    if (filter === "curated" && !a.is_curated) return false;
    if (search) {
      const q = search.toLowerCase();
      if (
        !a.name.toLowerCase().includes(q) &&
        !a.username.toLowerCase().includes(q)
      )
        return false;
    }
    return true;
  });

  const curatedCount = authors.filter((a) => a.is_curated).length;

  if (loading) {
    return (
      <div className="animate-pulse text-slate-400 py-20 text-center text-lg">
        {t("Carregando autores...", "Loading authors...")}
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">
        👥 {t("Autores", "Authors")}
      </h1>
      <p className="text-sm text-slate-500 mb-6">
        {t(
          `${authors.length} autores monitorados · ${curatedCount} líderes de opinião curados`,
          `${authors.length} monitored authors · ${curatedCount} curated opinion leaders`
        )}
      </p>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <input
          type="text"
          placeholder={t("Buscar autor...", "Search author...")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-64"
        />
        <div className="flex border border-slate-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filter === "all"
                ? "bg-primary text-white"
                : "bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {t("Todos", "All")}
          </button>
          <button
            onClick={() => setFilter("curated")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filter === "curated"
                ? "bg-primary text-white"
                : "bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            ⭐ {t("Líderes de Opinião", "Opinion Leaders")}
          </button>
        </div>
        <span className="text-sm text-slate-400 ml-auto">
          {filtered.length} {t("autores", "authors")}
        </span>
      </div>

      {filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map((a, i) => (
            <AuthorCard key={a.user_id} author={a} rank={i + 1} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon="👥"
          title={t("Nenhum autor encontrado", "No authors found")}
          subtitle={t("Tente outro termo de busca.", "Try another search term.")}
        />
      )}
    </div>
  );
}

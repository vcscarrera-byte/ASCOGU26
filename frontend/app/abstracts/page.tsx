"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Abstract } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
import AbstractCard from "@/components/AbstractCard";
import EmptyState from "@/components/EmptyState";
import FilterSidebar, { ActiveFilters } from "@/components/FilterSidebar";

export default function AbstractsPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [allAbstracts, setAllAbstracts] = useState<Abstract[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<ActiveFilters>({ tumors: [], drugs: [], sessionTypes: [] });

  useEffect(() => {
    async function load() {
      try {
        const abstracts = await fetch("/data/abstracts_all.json").then((r) => r.json());
        setAllAbstracts(abstracts);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const abstracts = useMemo(() => {
    let filtered = allAbstracts;

    // Text search
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.abstract_number.toLowerCase().includes(q) ||
          (a.presenter || "").toLowerCase().includes(q) ||
          (a.drugs || "").toLowerCase().includes(q) ||
          (a.tumor_type || "").toLowerCase().includes(q) ||
          (a.subjects || "").toLowerCase().includes(q) ||
          (a.body || "").toLowerCase().includes(q)
      );
    }

    // Tumor filter
    if (filters.tumors.length > 0) {
      filtered = filtered.filter((a) =>
        filters.tumors.some((tt) => (a.tumor_type || "").toLowerCase().includes(tt.toLowerCase()))
      );
    }

    // Drug filter
    if (filters.drugs.length > 0) {
      filtered = filtered.filter((a) =>
        filters.drugs.some((d) =>
          (a.drugs || "").toLowerCase().includes(d.toLowerCase()) ||
          a.title.toLowerCase().includes(d.toLowerCase())
        )
      );
    }

    // Session type filter
    if (filters.sessionTypes.length > 0) {
      filtered = filtered.filter((a) =>
        filters.sessionTypes.includes(a.session_type || "")
      );
    }

    return filtered;
  }, [allAbstracts, search, filters]);

  function navigateToDetail(abstractNumber: string) {
    router.push(`/abstracts/${abstractNumber}`);
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-6">
        {t("Abstracts \u2014 ASCO GU 2026", "Abstracts \u2014 ASCO GU 2026")}
      </h1>

      {/* Clinical Filters */}
      <FilterSidebar onFilterChange={setFilters} showSessionType />

      {/* Search */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
        <div className="relative w-full sm:w-80">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder={t("Buscar abstracts...", "Search abstracts...")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-3 sm:py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-full"
          />
        </div>
        <span className="text-sm text-slate-500">
          {abstracts.length} {t("resultados", "results")}
        </span>
      </div>

      {/* List */}
      {loading ? (
        <div className="animate-pulse text-slate-400 py-10 text-center">
          {t("Carregando dados...", "Loading data...")}
        </div>
      ) : abstracts.length > 0 ? (
        <div className="space-y-4">
          {abstracts.map((a, i) => (
            <AbstractCard
              key={a.abstract_number}
              abstract={a}
              rank={i + 1}
              onDetailClick={navigateToDetail}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon="🔬"
          title={t("Nenhum abstract encontrado", "No abstracts found")}
          subtitle={t(
            "Tente outro termo de busca ou ajuste os filtros.",
            "Try another search term or adjust the filters."
          )}
        />
      )}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { FilterOptions } from "@/lib/types";

interface FilterSidebarProps {
  onFilterChange: (filters: ActiveFilters) => void;
  showSessionType?: boolean;
}

export interface ActiveFilters {
  tumors: string[];
  drugs: string[];
  sessionTypes: string[];
}

export default function FilterSidebar({ onFilterChange, showSessionType = false }: FilterSidebarProps) {
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [tumors, setTumors] = useState<string[]>([]);
  const [drugs, setDrugs] = useState<string[]>([]);
  const [sessionTypes, setSessionTypes] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    api.getFilters().then(setOptions);
  }, []);

  useEffect(() => {
    onFilterChange({ tumors, drugs, sessionTypes });
  }, [tumors, drugs, sessionTypes]);

  const hasActive = tumors.length > 0 || drugs.length > 0 || sessionTypes.length > 0;

  const clearAll = () => {
    setTumors([]);
    setDrugs([]);
    setSessionTypes([]);
  };

  const toggleItem = (
    list: string[],
    setter: (v: string[]) => void,
    item: string
  ) => {
    if (list.includes(item)) {
      setter(list.filter((i) => i !== item));
    } else {
      setter([...list, item]);
    }
  };

  if (!options) return null;

  return (
    <div className="mb-6">
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
          hasActive
            ? "border-primary bg-primary-50 text-primary"
            : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
        }`}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
        </svg>
        Filtros Clínicos
        {hasActive && (
          <span className="bg-primary text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {tumors.length + drugs.length + sessionTypes.length}
          </span>
        )}
      </button>

      {/* Active filter badges */}
      {hasActive && (
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {tumors.map((t) => (
            <span
              key={t}
              onClick={() => toggleItem(tumors, setTumors, t)}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full cursor-pointer hover:bg-blue-100"
            >
              {t} ✕
            </span>
          ))}
          {drugs.map((d) => (
            <span
              key={d}
              onClick={() => toggleItem(drugs, setDrugs, d)}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-emerald-50 text-emerald-700 rounded-full cursor-pointer hover:bg-emerald-100"
            >
              {d} ✕
            </span>
          ))}
          {sessionTypes.map((s) => (
            <span
              key={s}
              onClick={() => toggleItem(sessionTypes, setSessionTypes, s)}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-violet-50 text-violet-700 rounded-full cursor-pointer hover:bg-violet-100"
            >
              {s} ✕
            </span>
          ))}
          <button
            onClick={clearAll}
            className="text-xs text-slate-400 hover:text-slate-600 ml-1"
          >
            Limpar todos
          </button>
        </div>
      )}

      {/* Filter panel */}
      {isOpen && (
        <div className="mt-3 bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
          {/* Tumor types */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Tipo de Tumor
            </label>
            <div className="flex flex-wrap gap-1.5">
              {options.tumor_types.map((t) => (
                <button
                  key={t}
                  onClick={() => toggleItem(tumors, setTumors, t)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
                    tumors.includes(t)
                      ? "bg-blue-500 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Drugs */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Medicação / Droga
            </label>
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
              {options.drug_names.map((d) => (
                <button
                  key={d}
                  onClick={() => toggleItem(drugs, setDrugs, d)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
                    drugs.includes(d)
                      ? "bg-emerald-500 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Session types (for abstracts) */}
          {showSessionType && options.session_types.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Tipo de Sessão
              </label>
              <div className="flex flex-wrap gap-1.5">
                {options.session_types.map((s) => (
                  <button
                    key={s}
                    onClick={() => toggleItem(sessionTypes, setSessionTypes, s)}
                    className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
                      sessionTypes.includes(s)
                        ? "bg-violet-500 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

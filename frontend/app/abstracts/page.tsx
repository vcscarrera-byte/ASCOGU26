"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { Abstract, Tweet } from "@/lib/types";
import AbstractCard from "@/components/AbstractCard";
import TweetCard from "@/components/TweetCard";
import EmptyState from "@/components/EmptyState";

export default function AbstractsPage() {
  const [allAbstracts, setAllAbstracts] = useState<Abstract[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedAbstract, setSelectedAbstract] = useState<Abstract | null>(null);
  const [linkedTweets, setLinkedTweets] = useState<Tweet[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);

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
    if (!search) return allAbstracts;
    const q = search.toLowerCase();
    return allAbstracts.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.abstract_number.toLowerCase().includes(q) ||
        (a.presenter || "").toLowerCase().includes(q) ||
        (a.drugs || "").toLowerCase().includes(q) ||
        (a.tumor_type || "").toLowerCase().includes(q) ||
        (a.body || "").toLowerCase().includes(q)
    );
  }, [allAbstracts, search]);

  async function openDetail(abstractNumber: string) {
    try {
      const res = await api.getAbstractDetail(abstractNumber);
      setSelectedAbstract(res.abstract);
      setLinkedTweets(res.linked_tweets);
      setDialogOpen(true);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-6">{"\uD83D\uDD2C"} Abstracts &mdash; ASCO GU 2026</h1>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Buscar abstracts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-80"
        />
        <span className="text-sm text-slate-500 ml-3">{abstracts.length} resultados</span>
      </div>

      {/* List */}
      {loading ? (
        <div className="animate-pulse text-slate-400 py-10 text-center">Carregando...</div>
      ) : abstracts.length > 0 ? (
        <div className="space-y-4">
          {abstracts.map((a, i) => (
            <AbstractCard
              key={a.abstract_number}
              abstract={a}
              rank={i + 1}
              onDetailClick={openDetail}
            />
          ))}
        </div>
      ) : (
        <EmptyState icon={"\uD83D\uDD2C"} title="Nenhum abstract encontrado" subtitle="Tente outro termo de busca." />
      )}

      {/* Detail Modal */}
      {dialogOpen && selectedAbstract && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setDialogOpen(false)}>
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-8 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">#{selectedAbstract.abstract_number}</h2>
                <h3 className="text-lg font-semibold text-slate-800 mt-1">{selectedAbstract.title}</h3>
              </div>
              <button onClick={() => setDialogOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
            </div>

            {selectedAbstract.body && !selectedAbstract.body.toLowerCase().includes("full, final text") && (
              <div className="prose prose-sm prose-slate max-w-none mb-6 border-t border-b border-slate-100 py-4">
                <p>{selectedAbstract.body}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm mb-6">
              {selectedAbstract.presenter && <div><strong>Apresentador:</strong> {selectedAbstract.presenter}</div>}
              {selectedAbstract.session_title && <div><strong>Sessao:</strong> {selectedAbstract.session_title}</div>}
              {selectedAbstract.tumor_type && <div><strong>Tumor:</strong> {selectedAbstract.tumor_type}</div>}
              {selectedAbstract.genes && <div><strong>Genes:</strong> {selectedAbstract.genes}</div>}
              {selectedAbstract.drugs && <div><strong>Drogas:</strong> {selectedAbstract.drugs}</div>}
              {selectedAbstract.organizations && <div><strong>Instituicoes:</strong> {selectedAbstract.organizations}</div>}
              {selectedAbstract.countries && <div><strong>Paises:</strong> {selectedAbstract.countries}</div>}
              {selectedAbstract.doi && <div><strong>DOI:</strong> {selectedAbstract.doi}</div>}
            </div>

            {linkedTweets.length > 0 && (
              <div>
                <h4 className="font-semibold text-slate-700 mb-3">{linkedTweets.length} tweets linkados</h4>
                <div className="space-y-3">
                  {linkedTweets.slice(0, 5).map((t) => (
                    <TweetCard key={t.tweet_id} tweet={t} compact />
                  ))}
                </div>
              </div>
            )}

            {selectedAbstract.url && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <a href={selectedAbstract.url} target="_blank" rel="noopener noreferrer"
                  className="text-primary hover:text-primary-dark font-medium hover:underline">
                  Ver no site da ASCO &rarr;
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Author } from "@/lib/types";
import AuthorCard from "@/components/AuthorCard";
import EmptyState from "@/components/EmptyState";

export default function AutoresPage() {
  const [authors, setAuthors] = useState<Author[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return <div className="animate-pulse text-slate-400 py-20 text-center text-lg">Carregando autores...</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-6">{"\uD83D\uDC64"} Autores</h1>

      {authors.length > 0 ? (
        <div className="space-y-3">
          {authors.map((a, i) => (
            <AuthorCard key={a.user_id} author={a} rank={i + 1} />
          ))}
        </div>
      ) : (
        <EmptyState icon={"\uD83D\uDC64"} title="Nenhum autor encontrado" />
      )}
    </div>
  );
}

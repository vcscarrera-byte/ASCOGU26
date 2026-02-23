"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type Lang = "pt" | "en";

interface I18nContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (pt: string, en: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  lang: "pt",
  setLang: () => {},
  t: (pt) => pt,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("pt");

  const t = (pt: string, en: string) => (lang === "pt" ? pt : en);

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}

// Translations dictionary
export const translations = {
  // Nav
  "nav.radar": { pt: "Radar", en: "Radar" },
  "nav.feed": { pt: "Feed", en: "Feed" },
  "nav.authors": { pt: "Autores", en: "Authors" },
  "nav.metrics": { pt: "Métricas", en: "Metrics" },
  "nav.abstracts": { pt: "Abstracts", en: "Abstracts" },

  // Home
  "home.subtitle": {
    pt: "Destaques dos líderes de opinião em uro-oncologia no ASCO GU 2026, ranqueados por relevância clínica.",
    en: "Highlights from key opinion leaders in uro-oncology at ASCO GU 2026, ranked by clinical relevance.",
  },
  "home.tweets": { pt: "Tweets", en: "Tweets" },
  "home.authors": { pt: "Autores", en: "Authors" },
  "home.kols": { pt: "Líderes de Opinião", en: "Key Opinion Leaders" },
  "home.abstracts": { pt: "Abstracts", en: "Abstracts" },
  "home.tab.highlights": { pt: "🔥 Destaques do Dia", en: "🔥 Today's Highlights" },
  "home.tab.congress": { pt: "🏆 Destaques do Congresso", en: "🏆 Congress Highlights" },
  "home.tab.abstracts": { pt: "📄 Abstracts em Alta", en: "📄 Trending Abstracts" },
  "home.tab.brief": { pt: "📝 Resumo IA", en: "📝 AI Summary" },

  // Feed
  "feed.title": { pt: "📰 Principais postagens", en: "📰 Top Posts" },
  "feed.search": { pt: "Buscar tweets...", en: "Search tweets..." },
  "feed.relevance": { pt: "Relevância", en: "Relevance" },
  "feed.engagement": { pt: "Engagement", en: "Engagement" },
  "feed.recent": { pt: "Recentes", en: "Recent" },
  "feed.tweets": { pt: "tweets", en: "tweets" },
  "feed.empty": { pt: "Nenhum tweet encontrado", en: "No tweets found" },
  "feed.emptyHint": { pt: "Tente outro termo de busca ou ajuste os filtros.", en: "Try another search term or adjust the filters." },

  // Authors
  "authors.title": { pt: "👥 Autores", en: "👥 Authors" },

  // Metrics
  "metrics.title": { pt: "📊 Métricas", en: "📊 Metrics" },

  // Abstracts
  "abstracts.title": { pt: "🔬 Abstracts — ASCO GU 2026", en: "🔬 Abstracts — ASCO GU 2026" },
  "abstracts.search": { pt: "Buscar abstracts...", en: "Search abstracts..." },
  "abstracts.results": { pt: "resultados", en: "results" },
  "abstracts.empty": { pt: "Nenhum abstract encontrado", en: "No abstracts found" },
  "abstracts.emptyHint": { pt: "Tente outro termo de busca ou ajuste os filtros.", en: "Try another search term or adjust the filters." },
  "abstracts.viewDetail": { pt: "Ver detalhe", en: "View detail" },
  "abstracts.viewOnASCO": { pt: "Ver no ASCO", en: "View on ASCO" },
  "abstracts.backToList": { pt: "Voltar para abstracts", en: "Back to abstracts" },
  "abstracts.notFound": { pt: "Abstract nao encontrado", en: "Abstract not found" },
  "abstracts.notFoundHint": { pt: "O abstract solicitado nao foi encontrado.", en: "The requested abstract was not found." },
  "abstracts.presenter": { pt: "Apresentador", en: "Presenter" },
  "abstracts.session": { pt: "Sessao", en: "Session" },
  "abstracts.tumor": { pt: "Tumor", en: "Tumor" },
  "abstracts.genes": { pt: "Genes", en: "Genes" },
  "abstracts.drugs": { pt: "Drogas", en: "Drugs" },
  "abstracts.organizations": { pt: "Instituicoes", en: "Organizations" },
  "abstracts.countries": { pt: "Paises", en: "Countries" },
  "abstracts.doi": { pt: "DOI", en: "DOI" },
  "abstracts.subjects": { pt: "Assuntos", en: "Subjects" },
  "abstracts.linkedTweets": { pt: "tweets linkados", en: "linked tweets" },

  // Filters
  "filters.title": { pt: "Filtros Clínicos", en: "Clinical Filters" },
  "filters.tumor": { pt: "Tipo de Tumor", en: "Tumor Type" },
  "filters.drug": { pt: "Medicação / Droga", en: "Drug / Medication" },
  "filters.session": { pt: "Tipo de Sessão", en: "Session Type" },
  "filters.clear": { pt: "Limpar todos", en: "Clear all" },

  // General
  "loading": { pt: "Carregando dados...", en: "Loading data..." },
  "empty.noBrief": { pt: "Nenhum resumo disponível", en: "No summary available" },
  "empty.noBriefHint": { pt: "O resumo IA será gerado após a coleta de dados.", en: "The AI summary will be generated after data collection." },
} as const;

export type TranslationKey = keyof typeof translations;

export function useTranslation() {
  const { lang } = useI18n();
  return (key: TranslationKey) => translations[key][lang];
}

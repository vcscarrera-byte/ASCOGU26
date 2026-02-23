"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n, useTranslation } from "@/lib/i18n";

const navItems = [
  { href: "/", labelKey: "nav.radar" as const, icon: "📡" },
  { href: "/feed", labelKey: "nav.feed" as const, icon: "📰" },
  { href: "/autores", labelKey: "nav.authors" as const, icon: "👥" },
  { href: "/metricas", labelKey: "nav.metrics" as const, icon: "📊" },
  { href: "/abstracts", labelKey: "nav.abstracts" as const, icon: "🔬" },
];

export default function NavBar() {
  const { lang, setLang } = useI18n();
  const t = useTranslation();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <Link href="/" className="text-lg font-bold text-primary tracking-tight">
            📡 ASCO GU RADAR
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-3">
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? "bg-primary-50 text-primary"
                        : "text-slate-600 hover:text-primary hover:bg-primary-50"
                    }`}
                  >
                    {item.icon} {t(item.labelKey)}
                  </Link>
                );
              })}
            </nav>

            {/* Language toggle - desktop */}
            <div className="inline-flex rounded-md border border-slate-200 overflow-hidden ml-2">
              <button
                onClick={() => setLang("pt")}
                className={`px-2 py-1 text-xs font-medium transition-colors ${
                  lang === "pt"
                    ? "bg-primary text-white"
                    : "bg-white text-slate-500 hover:bg-slate-50"
                }`}
              >
                PT
              </button>
              <button
                onClick={() => setLang("en")}
                className={`px-2 py-1 text-xs font-medium transition-colors ${
                  lang === "en"
                    ? "bg-primary text-white"
                    : "bg-white text-slate-500 hover:bg-slate-50"
                }`}
              >
                EN
              </button>
            </div>
          </div>

          {/* Mobile: language toggle + hamburger */}
          <div className="flex md:hidden items-center gap-2">
            {/* Language toggle - mobile */}
            <div className="inline-flex rounded-md border border-slate-200 overflow-hidden">
              <button
                onClick={() => setLang("pt")}
                className={`px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  lang === "pt"
                    ? "bg-primary text-white"
                    : "bg-white text-slate-500"
                }`}
              >
                PT
              </button>
              <button
                onClick={() => setLang("en")}
                className={`px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  lang === "en"
                    ? "bg-primary text-white"
                    : "bg-white text-slate-500"
                }`}
              >
                EN
              </button>
            </div>

            {/* Hamburger button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Toggle menu"
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile slide-down menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white">
          <nav className="px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-3 text-base font-medium rounded-lg transition-colors ${
                    isActive
                      ? "bg-primary-50 text-primary"
                      : "text-slate-600 hover:text-primary hover:bg-slate-50"
                  }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  {t(item.labelKey)}
                  {isActive && (
                    <span className="ml-auto w-2 h-2 rounded-full bg-primary" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}

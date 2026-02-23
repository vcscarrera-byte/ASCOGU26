"use client";

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

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <Link href="/" className="text-lg font-bold text-primary tracking-tight">
            📡 ASCO GU RADAR
          </Link>

          <div className="flex items-center gap-3">
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
                    <span className="hidden sm:inline">{item.icon} </span>
                    {t(item.labelKey)}
                  </Link>
                );
              })}
            </nav>

            {/* Language toggle */}
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
        </div>
      </div>
    </header>
  );
}

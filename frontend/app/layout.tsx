import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ASCO GU RADAR 2026",
  description: "Destaques dos KOLs de uro-oncologia no ASCO GU 2026",
};

const navItems = [
  { href: "/", label: "Radar", icon: "\uD83D\uDCE1" },
  { href: "/feed", label: "Feed", icon: "\uD83D\uDCF0" },
  { href: "/autores", label: "Autores", icon: "\uD83D\uDC64" },
  { href: "/metricas", label: "Metricas", icon: "\uD83D\uDCCA" },
  { href: "/abstracts", label: "Abstracts", icon: "\uD83D\uDD2C" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-50 text-slate-900 font-sans antialiased">
        {/* Top nav */}
        <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              <Link href="/" className="text-lg font-bold text-primary tracking-tight">
                {"\uD83D\uDCE1"} ASCO GU RADAR
              </Link>
              <nav className="flex items-center gap-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-primary hover:bg-primary-50 rounded-lg transition-colors"
                  >
                    <span className="hidden sm:inline">{item.icon} </span>
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-400">
          ASCO GU RADAR 2026 &middot; Feb 26-28, San Francisco
        </footer>
      </body>
    </html>
  );
}

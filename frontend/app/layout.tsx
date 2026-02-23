import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "ASCO GU RADAR 2026",
  description: "Destaques dos líderes de opinião em uro-oncologia no ASCO GU 2026",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-50 text-slate-900 font-sans antialiased">
        <I18nProvider>
          <NavBar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-400">
            ASCO GU RADAR 2026 &middot; Feb 26-28, San Francisco
          </footer>
        </I18nProvider>
        <Analytics />
      </body>
    </html>
  );
}

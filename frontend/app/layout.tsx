import type { Metadata, Viewport } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";
import NavBar from "@/components/NavBar";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#2563eb",
};

export const metadata: Metadata = {
  title: "ASCO GU RADAR 2026",
  description:
    "Real-time monitoring dashboard for ASCO GU 2026. Highlights from key opinion leaders in uro-oncology, ranked by clinical relevance. Feb 26-28, San Francisco.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📡</text></svg>",
  },
  openGraph: {
    title: "ASCO GU RADAR 2026",
    description:
      "Real-time highlights from key opinion leaders in uro-oncology at ASCO GU 2026, ranked by clinical relevance.",
    siteName: "ASCO GU RADAR 2026",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "ASCO GU RADAR 2026",
    description:
      "Real-time highlights from key opinion leaders in uro-oncology at ASCO GU 2026, ranked by clinical relevance.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-50 text-slate-900 font-sans antialiased overflow-x-hidden">
        <I18nProvider>
          <NavBar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            {children}
          </main>
          <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-400 px-4">
            ASCO GU RADAR 2026 &middot; Feb 26-28, San Francisco
          </footer>
        </I18nProvider>
        <Analytics />
      </body>
    </html>
  );
}

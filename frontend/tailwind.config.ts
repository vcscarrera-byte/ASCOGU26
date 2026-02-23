import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#2563eb",
          light: "#3b82f6",
          dark: "#1d4ed8",
          50: "#eff6ff",
          100: "#dbeafe",
        },
        accent: "#0ea5e9",
        clinical: {
          tumor: "#3b82f6",
          drug: "#10b981",
          gene: "#8b5cf6",
          relevance: "#ef4444",
          buzz: "#8b5cf6",
          oral: "#ef4444",
          rapidoral: "#f59e0b",
          poster: "#6b7280",
          general: "#8b5cf6",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;

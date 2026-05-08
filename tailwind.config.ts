import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        vigil: {
          bg: "#0f172a",
          card: "#1e293b",
          "trust-high": "#34d399",
          "trust-medium": "#fbbf24",
          "trust-low": "#f43f5e",
          accent: "#38bdf8",
          "text-primary": "#f1f5f9",
          "text-secondary": "#94a3b8",
          border: "#334155",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;

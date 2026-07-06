import type { Config } from "tailwindcss";

/**
 * Beige Claude UI — Tailwind theme tokens.
 * Merge the `extend` block into your existing tailwind.config.ts if you
 * already have one; otherwise use this file as-is.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cocoa: {
          DEFAULT: "#17110D", // page background (deep, near-black chocolate)
          panel: "#211913", // composer / dropdown surface
          elevated: "#261D16", // raised surfaces (composer body)
          bubble: "#271E16", // user message bubble
          border: "#332821", // AA-safe hairline borders
          "bubble-border": "#3A2E24",
          hover: "#2A2019", // subtle hover wash
        },
        cream: "#F4EFE6", // primary text
        muted: "#AB9C84", // secondary text / idle icons
        faint: "#84765F", // disclaimer / lowest-emphasis text
        gold: {
          DEFAULT: "#C9A567", // brushed-brass accent
          bright: "#DEC084", // accent hover / emphasis
          dim: "#6E5A38", // low-emphasis borders, dividers
          deep: "#4E3F28", // background tints behind gold content
        },
      },
      fontFamily: {
        // system sans for UI chrome; serif for assistant prose
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        serif: ["var(--font-serif)", "Georgia", "serif"],
      },
      boxShadow: {
        "premium-sm": "0 1px 2px rgba(0,0,0,0.35)",
        "premium-md":
          "0 10px 28px -10px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3)",
        "premium-lg":
          "0 24px 60px -16px rgba(0,0,0,0.6), 0 6px 16px rgba(0,0,0,0.35)",
        "inner-top": "inset 0 1px 0 rgba(255,255,255,0.035)",
      },
      keyframes: {
        "token-in": {
          "0%": { opacity: "0", filter: "blur(4px)" },
          "100%": { opacity: "1", filter: "blur(0)" },
        },
      },
      animation: {
        "token-in": "token-in 0.45s ease forwards",
      },
    },
  },
  plugins: [],
};

export default config;

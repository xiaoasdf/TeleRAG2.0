import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f1e7",
        foreground: "#1c1917",
        card: "#fffaf3",
        border: "#d7c6af",
        accent: "#b5522d",
        primary: "#1f453b",
        muted: "#6b655f",
        destructive: "#8b2e2e"
      },
      boxShadow: {
        paper: "0 16px 40px rgba(44, 32, 19, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;

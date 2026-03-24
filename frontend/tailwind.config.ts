import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        primary: "#2c2218",
        secondary: "#5c4a3a",
        accent: "#8b7355",
        background: "#fffef9",
        surface: "#faf8f3",
        text: "#2c2218",
        textSecondary: "#6b5d4f",
        border: "#e8e2d8",
        "trust-high": "#3d6b4f",
        "trust-medium": "#8b7355",
        "trust-low": "#8b4f4f",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        slideDown: {
          "0%": { opacity: "0", maxHeight: "0" },
          "100%": { opacity: "1", maxHeight: "500px" },
        },
        ringFill: {
          "0%": { strokeDashoffset: "283" },
        },
      },
      animation: {
        fadeIn: "fadeIn 0.5s ease-out forwards",
        fadeInUp: "fadeInUp 0.6s ease-out forwards",
        scaleIn: "scaleIn 0.4s ease-out forwards",
        slideDown: "slideDown 0.3s ease-out forwards",
        ringFill: "ringFill 1s ease-out forwards",
      },
    },
  },
  plugins: [],
};
export default config;
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2c2218",
        secondary: "#5c4a3a",
        accent: "#8b7355",
        background: "#fffef9",
        surface: "#faf8f3",
        text: "#2c2218",
        textSecondary: "#6b5d4f",
        border: "#e8e2d8",
      },
    },
  },
  plugins: [],
};
export default config;
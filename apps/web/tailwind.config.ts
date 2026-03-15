import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#102033",
        paper: "#f7f1e8",
        accent: "#ef8d32",
        slate: "#55708e",
      },
      boxShadow: {
        soft: "0 24px 80px rgba(16, 32, 51, 0.12)",
      },
      fontFamily: {
        sans: ["Trebuchet MS", "Verdana", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}", "./e2e/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        panel: "#f8fafc",
        line: "#d7dee8",
        teal: "#0f766e",
        saffron: "#b45309",
        berry: "#be123c"
      },
      boxShadow: {
        focus: "0 0 0 3px rgba(15, 118, 110, 0.18)"
      }
    }
  },
  plugins: []
};

export default config;


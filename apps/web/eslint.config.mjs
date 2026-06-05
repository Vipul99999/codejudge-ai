import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: [".next/**", "node_modules/**", "coverage/**", "playwright-report/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}", "tests/**/*.{ts,tsx}", "e2e/**/*.ts"],
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
      globals: {
        React: "readonly",
        JSX: "readonly",
      },
    },
  },
];

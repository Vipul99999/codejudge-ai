import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Language, ModuleKey } from "@/lib/schemas";

type HistoryEntry = {
  id: string;
  module: ModuleKey;
  score?: number;
  createdAt: string;
  summary: string;
};

type EvaluationState = {
  activeModule: ModuleKey;
  language: Language;
  history: HistoryEntry[];
  setActiveModule: (module: ModuleKey) => void;
  setLanguage: (language: Language) => void;
  addHistory: (entry: Omit<HistoryEntry, "id" | "createdAt">) => void;
};

export const useEvaluationStore = create<EvaluationState>()(
  persist(
    (set) => ({
      activeModule: "analyze",
      language: "python",
      history: [],
      setActiveModule: (module) => set({ activeModule: module }),
      setLanguage: (language) => set({ language }),
      addHistory: (entry) =>
        set((state) => ({
          history: [
            {
              ...entry,
              id: crypto.randomUUID(),
              createdAt: new Date().toISOString(),
            },
            ...state.history,
          ].slice(0, 20),
        })),
    }),
    { name: "codejudge-ai-state" },
  ),
);

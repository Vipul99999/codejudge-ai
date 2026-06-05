import {
  BarChart3,
  Binary,
  Bug,
  ClipboardCheck,
  Code2,
  GitCompare,
  Layers3,
  ListChecks,
  Microscope,
  Scale,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ModuleKey } from "@/lib/schemas";

export type ModuleConfig = {
  key: ModuleKey;
  label: string;
  description: string;
  icon: LucideIcon;
};

export const modules: ModuleConfig[] = [
  {
    key: "analyze",
    label: "Code Analyzer",
    description: "Quality scores, risks, and improvement suggestions.",
    icon: Code2,
  },
  {
    key: "bugs",
    label: "Bug Detector",
    description: "Null, boundary, recursion, async, and memory risks.",
    icon: Bug,
  },
  {
    key: "test-cases",
    label: "Test Case Generator",
    description: "Normal, edge, corner, and stress cases with export.",
    icon: ListChecks,
  },
  {
    key: "complexity",
    label: "Complexity Analyzer",
    description: "Time, space, explanation, and confidence score.",
    icon: Binary,
  },
  {
    key: "compare",
    label: "Solution Comparator",
    description: "Compare two implementations across evaluator criteria.",
    icon: GitCompare,
  },
  {
    key: "llm-evaluate",
    label: "LLM Code Evaluator",
    description: "Instruction following, hallucination, safety, and code quality.",
    icon: Microscope,
  },
  {
    key: "reasoning",
    label: "Reasoning Reviewer",
    description: "Audit logic chains, assumptions, and contradictions.",
    icon: ClipboardCheck,
  },
  {
    key: "dataset",
    label: "Dataset Builder",
    description: "Generate evaluator datasets and JSON or CSV exports.",
    icon: Layers3,
  },
  {
    key: "rubric",
    label: "Rubric Engine",
    description: "Create weighted scoring rubrics for evaluation workflows.",
    icon: Scale,
  },
];

export const dashboardModule = { label: "Benchmark Dashboard", icon: BarChart3 };

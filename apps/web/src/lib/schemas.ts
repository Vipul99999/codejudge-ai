import { z } from "zod";

export const languageSchema = z.enum(["python", "javascript", "typescript", "java", "cpp"]);
export type Language = z.infer<typeof languageSchema>;

export const categoryScoreSchema = z.object({
  name: z.string(),
  score: z.number(),
  rationale: z.string(),
});

export const findingSchema = z.object({
  category: z.string(),
  severity: z.string(),
  explanation: z.string(),
  likely_impact: z.string(),
  recommended_fix: z.string(),
  line: z.number().nullable().optional(),
});

export const testCaseSchema = z.object({
  case_type: z.string(),
  input: z.string(),
  expected_output: z.string(),
  reason: z.string(),
});

export const benchmarkSchema = z.object({
  evaluations_performed: z.number(),
  average_score: z.number(),
  common_bug_categories: z.array(z.record(z.number())),
  complexity_distribution: z.array(z.record(z.number())),
  module_distribution: z.array(z.record(z.number())),
});

export type BenchmarkSummary = z.infer<typeof benchmarkSchema>;

export type ApiResult = Record<string, unknown>;

export type ModuleKey =
  | "analyze"
  | "bugs"
  | "test-cases"
  | "complexity"
  | "compare"
  | "llm-evaluate"
  | "reasoning"
  | "dataset"
  | "rubric";

export const endpointByModule: Record<ModuleKey, string> = {
  analyze: "/api/analyze",
  bugs: "/api/bugs",
  "test-cases": "/api/test-cases",
  complexity: "/api/complexity",
  compare: "/api/compare",
  "llm-evaluate": "/api/llm-evaluate",
  reasoning: "/api/reasoning",
  dataset: "/api/dataset",
  rubric: "/api/rubric",
};

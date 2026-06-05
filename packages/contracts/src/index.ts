import { z } from "zod";

export const scoreSchema = z.number().min(0).max(100);
export const confidenceScoreSchema = z.number().min(0).max(1);

export const languageSchema = z.enum(["python", "javascript", "typescript", "java", "cpp"]);

export const supportTierSchema = z.enum(["tier_1", "tier_2", "tier_3", "unsupported"]);

export const inputTypeSchema = z.enum([
  "source_code",
  "prompt_response",
  "reasoning_trace",
  "rubric",
  "dataset_item",
  "solution_pair",
]);

export const evaluationTypeSchema = z.enum([
  "code_review",
  "bug_risk",
  "test_generation",
  "complexity",
  "solution_comparison",
  "ai_response",
  "reasoning",
  "dataset_build",
  "rubric_score",
  "benchmark_summary",
]);

export const severitySchema = z.enum(["critical", "high", "medium", "low", "info"]);
export const probabilitySchema = z.enum(["high", "medium", "low", "unknown"]);
export const exportFormatSchema = z.enum(["json", "csv", "parquet"]);
export const difficultySchema = z.enum(["easy", "medium", "hard", "mixed"]);

export const sourceSpanSchema = z.object({
  startLine: z.number().int().min(1),
  startColumn: z.number().int().min(1),
  endLine: z.number().int().min(1),
  endColumn: z.number().int().min(1),
  snippet: z.string().max(2_000).optional(),
});

export const evidenceSchema = z.object({
  id: z.string().min(1),
  kind: z.enum(["ast_node", "token_pattern", "metric", "rubric_match", "text_pattern"]),
  message: z.string().min(1),
  ruleId: z.string().min(1),
  span: sourceSpanSchema.optional(),
  metricName: z.string().min(1).optional(),
  metricValue: z.union([z.number(), z.string(), z.boolean()]).optional(),
});

export const limitationSchema = z.object({
  id: z.string().min(1),
  scope: z.enum(["parser", "language", "static_analysis", "rubric", "input", "engine"]),
  message: z.string().min(1),
});

export const detectedPatternSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  category: z.string().min(1),
  confidence: confidenceScoreSchema,
  evidenceIds: z.array(z.string().min(1)),
});

export const scoreBreakdownSchema = z.object({
  category: z.string().min(1),
  score: scoreSchema,
  weight: z.number().min(0).max(1),
  why: z.string().min(1),
  evidenceIds: z.array(z.string().min(1)),
});

export const findingSchema = z.object({
  id: z.string().min(1),
  ruleId: z.string().min(1),
  title: z.string().min(1),
  category: z.string().min(1),
  severity: severitySchema,
  probability: probabilitySchema,
  scoreImpact: z.number().min(-100).max(100),
  confidence: confidenceScoreSchema,
  evidenceIds: z.array(z.string().min(1)),
  why: z.string().min(1),
  recommendation: z.string().min(1).optional(),
});

export const baseEvaluationResultSchema = z.object({
  id: z.string().min(1),
  evaluationType: evaluationTypeSchema,
  score: scoreSchema,
  confidence: confidenceScoreSchema,
  evidence: z.array(evidenceSchema),
  limitations: z.array(limitationSchema),
  detectedPatterns: z.array(detectedPatternSchema),
  findings: z.array(findingSchema),
  breakdown: z.array(scoreBreakdownSchema),
  why: z.string().min(1),
  engineVersion: z.string().min(1),
  rubricVersionId: z.string().min(1).optional(),
  createdAt: z.string().datetime(),
});

export const artifactRefSchema = z.object({
  id: z.string().min(1),
  inputType: inputTypeSchema,
  checksum: z.string().min(32),
  language: languageSchema.optional(),
  sizeBytes: z.number().int().min(0),
});

export const codeArtifactSchema = z.object({
  language: languageSchema,
  source: z.string().min(1).max(120_000),
  filename: z.string().max(240).optional(),
});

export const promptResponseArtifactSchema = z.object({
  prompt: z.string().min(1).max(40_000),
  response: z.string().min(1).max(120_000),
  language: languageSchema.optional(),
});

export const reasoningArtifactSchema = z.object({
  problem: z.string().min(1).max(40_000),
  reasoning: z.string().min(1).max(80_000),
});

export const rubricCriterionSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1).max(120),
  description: z.string().min(1).max(2_000),
  weight: z.number().min(0).max(1),
  minimumEvidence: z.number().int().min(0).max(20),
});

export const rubricVersionSchema = z.object({
  id: z.string().min(1),
  rubricId: z.string().min(1),
  version: z.number().int().min(1),
  name: z.string().min(1).max(120),
  criteria: z.array(rubricCriterionSchema).min(1).max(20),
  checksum: z.string().min(32),
  createdAt: z.string().datetime(),
});

export const analysisRequestSchema = z.object({
  workspaceId: z.string().min(1),
  evaluationType: evaluationTypeSchema,
  artifact: z.union([codeArtifactSchema, promptResponseArtifactSchema, reasoningArtifactSchema]),
  rubricVersionId: z.string().min(1).optional(),
});

export const compareSolutionsRequestSchema = z.object({
  workspaceId: z.string().min(1),
  language: languageSchema,
  solutionA: z.string().min(1).max(120_000),
  solutionB: z.string().min(1).max(120_000),
  rubricVersionId: z.string().min(1).optional(),
});

export const datasetItemSchema = z.object({
  id: z.string().min(1),
  problem: z.string().min(1),
  solution: z.string().min(1),
  rubricVersionId: z.string().min(1),
  tests: z.array(
    z.object({
      id: z.string().min(1),
      kind: z.enum(["happy_path", "edge", "corner", "stress", "negative", "mutation", "property"]),
      description: z.string().min(1),
      input: z.string().min(1),
      expectedBehavior: z.string().min(1),
      evidenceIds: z.array(z.string().min(1)),
    }),
  ),
  difficulty: difficultySchema.exclude(["mixed"]),
  tags: z.array(z.string().min(1).max(64)),
});

export const benchmarkEventSchema = z.object({
  id: z.string().min(1),
  evaluationId: z.string().min(1),
  workspaceId: z.string().min(1),
  evaluationType: evaluationTypeSchema,
  language: languageSchema.optional(),
  score: scoreSchema,
  confidence: confidenceScoreSchema,
  latencyMs: z.number().int().min(0),
  failureCategories: z.array(z.string().min(1)),
  engineVersion: z.string().min(1),
  rubricVersionId: z.string().min(1).optional(),
  occurredAt: z.string().datetime(),
});

export const exportRequestSchema = z.object({
  workspaceId: z.string().min(1),
  resourceType: z.enum(["evaluation", "dataset", "benchmark"]),
  resourceId: z.string().min(1),
  format: exportFormatSchema,
});

export const apiErrorSchema = z.object({
  code: z.string().min(1),
  message: z.string().min(1),
  requestId: z.string().min(1),
});

export type Language = z.infer<typeof languageSchema>;
export type EvaluationType = z.infer<typeof evaluationTypeSchema>;
export type BaseEvaluationResult = z.infer<typeof baseEvaluationResultSchema>;
export type AnalysisRequest = z.infer<typeof analysisRequestSchema>;
export type CompareSolutionsRequest = z.infer<typeof compareSolutionsRequestSchema>;
export type RubricVersion = z.infer<typeof rubricVersionSchema>;
export type DatasetItem = z.infer<typeof datasetItemSchema>;
export type BenchmarkEvent = z.infer<typeof benchmarkEventSchema>;
export type ExportRequest = z.infer<typeof exportRequestSchema>;

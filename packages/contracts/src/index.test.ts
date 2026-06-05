import { describe, expect, it } from "vitest";

import { analysisRequestSchema, baseEvaluationResultSchema, rubricVersionSchema } from "./index";

describe("CodeJudge shared contracts", () => {
  it("accepts a code analysis request with a language and source artifact", () => {
    const request = analysisRequestSchema.parse({
      workspaceId: "workspace-default",
      evaluationType: "code_review",
      artifact: {
        language: "python",
        source: "def add(a, b):\n    return a + b\n",
      },
    });

    expect(request.evaluationType).toBe("code_review");
  });

  it("requires every evaluation result to expose trust-layer fields", () => {
    const result = baseEvaluationResultSchema.parse({
      id: "eval-1",
      evaluationType: "code_review",
      score: 82,
      confidence: 0.74,
      evidence: [
        {
          id: "evidence-1",
          kind: "metric",
          message: "Cyclomatic complexity is 2.",
          ruleId: "complexity.cyclomatic",
          metricName: "cyclomatic_complexity",
          metricValue: 2,
        },
      ],
      limitations: [
        {
          id: "limitation-1",
          scope: "static_analysis",
          message: "Static analysis cannot prove runtime correctness.",
        },
      ],
      detectedPatterns: [],
      findings: [],
      breakdown: [
        {
          category: "maintainability",
          score: 82,
          weight: 0.4,
          why: "Low branching and direct return path.",
          evidenceIds: ["evidence-1"],
        },
      ],
      why: "Score is derived from parser-backed structure and metric evidence.",
      engineVersion: "0.1.0",
      createdAt: "2026-06-05T00:00:00.000Z",
    });

    expect(result.evidence).toHaveLength(1);
    expect(result.limitations).toHaveLength(1);
  });

  it("freezes rubric versions with normalized criteria", () => {
    const rubric = rubricVersionSchema.parse({
      id: "rubric-version-1",
      rubricId: "rubric-1",
      version: 1,
      name: "Code review baseline",
      checksum: "0123456789abcdef0123456789abcdef",
      createdAt: "2026-06-05T00:00:00.000Z",
      criteria: [
        {
          id: "quality",
          name: "Quality",
          description: "Maintainable and clear implementation.",
          weight: 1,
          minimumEvidence: 1,
        },
      ],
    });

    expect(rubric.criteria[0]?.weight).toBe(1);
  });
});

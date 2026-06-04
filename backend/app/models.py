from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Language(str, Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    cpp = "cpp"


class Confidence(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class AnalysisBase(BaseModel):
    confidence: Confidence = Confidence.medium
    reason: str = "Static analysis only"
    limitations: list[str] = Field(default_factory=list)


class CodeRequest(BaseModel):
    language: Language
    code: str = Field(min_length=1, max_length=80_000)


class CompareRequest(BaseModel):
    language: Language
    solution_a: str = Field(min_length=1, max_length=80_000)
    solution_b: str = Field(min_length=1, max_length=80_000)


class LlmEvaluationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    ai_response: str = Field(min_length=1, max_length=80_000)
    language: Language | None = None


class ReasoningRequest(BaseModel):
    problem: str = Field(min_length=1, max_length=20_000)
    reasoning: str = Field(min_length=1, max_length=40_000)


class DatasetRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    language: Language = Language.python
    count: int = Field(default=5, ge=1, le=25)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"
    tags: list[str] = Field(default_factory=list, max_length=12)


class RubricCategory(BaseModel):
    name: str
    weight: float = Field(ge=0)
    score: float = Field(ge=0, le=100)


class RubricRequest(BaseModel):
    categories: list[RubricCategory] = Field(min_length=1, max_length=12)


class CategoryScore(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    rationale: str


class Finding(BaseModel):
    category: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    explanation: str
    likely_impact: str
    recommended_fix: str
    line: int | None = None


class CodeAnalysisResponse(AnalysisBase):
    overall_score: int = Field(ge=0, le=100)
    category_scores: list[CategoryScore]
    suggestions: list[str]
    risk_summary: list[str]
    signals: dict[str, Any] = Field(default_factory=dict)


class BugDetectorResponse(AnalysisBase):
    findings: list[Finding]
    summary: str


class TestCase(BaseModel):
    case_type: Literal["normal", "edge", "corner", "stress"]
    input: str
    expected_output: str
    reason: str


class TestCaseResponse(AnalysisBase):
    cases: list[TestCase]
    export: dict[str, str]


class ComplexityResponse(AnalysisBase):
    time_complexity: str
    space_complexity: str
    explanation: str
    confidence_score: int = Field(ge=0, le=100)


class ComparisonResponse(AnalysisBase):
    winner: Literal["A", "B", "Tie"]
    reason_summary: str
    score_breakdown: list[CategoryScore]
    solution_a_score: int
    solution_b_score: int


class LlmEvaluationResponse(AnalysisBase):
    overall_score: int = Field(ge=0, le=100)
    report: list[CategoryScore]
    hallucination_risks: list[str]
    safety_notes: list[str]


class ReasoningResponse(AnalysisBase):
    score: int = Field(ge=0, le=100)
    feedback: list[str]
    missing_assumptions: list[str]
    contradictions: list[str]


class DatasetItem(BaseModel):
    problem: str
    solution: str
    test_cases: list[TestCase]
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str]


class DatasetResponse(AnalysisBase):
    items: list[DatasetItem]
    export: dict[str, str]


class RubricResponse(AnalysisBase):
    weighted_score: float
    normalized_categories: list[RubricCategory]
    interpretation: str


class BenchmarkEvent(BaseModel):
    module: str
    score: int = Field(ge=0, le=100)
    language: Language | None = None
    bug_categories: list[str] = Field(default_factory=list)
    complexity: str | None = None


class BenchmarkSummary(BaseModel):
    evaluations_performed: int
    average_score: float
    common_bug_categories: list[dict[str, int]]
    complexity_distribution: list[dict[str, int]]
    module_distribution: list[dict[str, int]]

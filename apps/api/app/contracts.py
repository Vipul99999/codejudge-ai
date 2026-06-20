from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Score = Annotated[float, Field(ge=0, le=100)]
ConfidenceScore = Annotated[float, Field(ge=0, le=1)]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Language(str, Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    cpp = "cpp"


class SupportTier(str, Enum):
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"
    unsupported = "unsupported"


class InputType(str, Enum):
    source_code = "source_code"
    prompt_response = "prompt_response"
    reasoning_trace = "reasoning_trace"
    rubric = "rubric"
    dataset_item = "dataset_item"
    solution_pair = "solution_pair"


class EvaluationType(str, Enum):
    code_review = "code_review"
    bug_risk = "bug_risk"
    test_generation = "test_generation"
    complexity = "complexity"
    solution_comparison = "solution_comparison"
    ai_response = "ai_response"
    reasoning = "reasoning"
    dataset_build = "dataset_build"
    rubric_score = "rubric_score"
    benchmark_summary = "benchmark_summary"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Probability(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"


class ExportFormat(str, Enum):
    json = "json"
    csv = "csv"
    parquet = "parquet"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    mixed = "mixed"


class SourceSpan(ContractModel):
    start_line: int = Field(ge=1)
    start_column: int = Field(ge=1)
    end_line: int = Field(ge=1)
    end_column: int = Field(ge=1)
    snippet: str | None = Field(default=None, max_length=2_000)


class Evidence(ContractModel):
    id: str = Field(min_length=1)
    kind: Literal["ast_node", "token_pattern", "metric", "rubric_match", "text_pattern"]
    message: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    span: SourceSpan | None = None
    metric_name: str | None = Field(default=None, min_length=1)
    metric_value: int | float | str | bool | None = None


class Limitation(ContractModel):
    id: str = Field(min_length=1)
    scope: Literal["parser", "language", "static_analysis", "rubric", "input", "engine"]
    message: str = Field(min_length=1)


class DetectedPattern(ContractModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    confidence: ConfidenceScore
    evidence_ids: list[str] = Field(default_factory=list)


class ScoreBreakdown(ContractModel):
    category: str = Field(min_length=1)
    score: Score
    weight: float = Field(ge=0, le=1)
    why: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class Finding(ContractModel):
    id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    severity: Severity
    probability: Probability
    score_impact: float = Field(ge=-100, le=100)
    confidence: ConfidenceScore
    evidence_ids: list[str] = Field(default_factory=list)
    why: str = Field(min_length=1)
    recommendation: str | None = Field(default=None, min_length=1)


class ArtifactRef(ContractModel):
    id: str = Field(min_length=1)
    input_type: InputType
    checksum: str = Field(min_length=32)
    language: Language | None = None
    size_bytes: int = Field(ge=0)


class WorkspaceEntity(ContractModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    created_at: datetime
    updated_at: datetime


class RubricCriterion(ContractModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2_000)
    weight: float = Field(ge=0, le=1)
    minimum_evidence: int = Field(default=1, ge=0, le=20)


class RubricVersionEntity(ContractModel):
    id: str = Field(min_length=1)
    rubric_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    criteria: list[RubricCriterion] = Field(min_length=1, max_length=20)
    checksum: str = Field(min_length=32)
    created_at: datetime


class EvaluationEntity(ContractModel):
    id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    artifact_ref: ArtifactRef
    evaluation_type: EvaluationType
    engine_version: str = Field(min_length=1)
    rubric_version_id: str | None = Field(default=None, min_length=1)
    score: Score
    confidence: ConfidenceScore
    created_at: datetime


class DatasetItemEntity(ContractModel):
    id: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    solution: str = Field(min_length=1)
    rubric_version_id: str = Field(min_length=1)
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str] = Field(default_factory=list, max_length=20)


class BenchmarkEventEntity(ContractModel):
    id: str = Field(min_length=1)
    evaluation_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    evaluation_type: EvaluationType
    language: Language | None = None
    score: Score
    confidence: ConfidenceScore
    latency_ms: int = Field(ge=0)
    failure_categories: list[str] = Field(default_factory=list)
    engine_version: str = Field(min_length=1)
    rubric_version_id: str | None = Field(default=None, min_length=1)
    occurred_at: datetime


class ExportArtifactEntity(ContractModel):
    id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    resource_type: Literal["evaluation", "dataset", "benchmark"]
    resource_id: str = Field(min_length=1)
    format: ExportFormat
    checksum: str = Field(min_length=32)
    created_at: datetime


class AuditEventEntity(ContractModel):
    id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    occurred_at: datetime


class CodeArtifactDTO(ContractModel):
    language: Language
    source: str = Field(min_length=1, max_length=120_000)
    filename: str | None = Field(default=None, max_length=240)


class PromptResponseArtifactDTO(ContractModel):
    prompt: str = Field(min_length=1, max_length=40_000)
    response: str = Field(min_length=1, max_length=120_000)
    language: Language | None = None


class ReasoningArtifactDTO(ContractModel):
    problem: str = Field(min_length=1, max_length=40_000)
    reasoning: str = Field(min_length=1, max_length=80_000)


class AnalysisRequestDTO(ContractModel):
    workspace_id: str = Field(min_length=1)
    evaluation_type: EvaluationType
    artifact: CodeArtifactDTO | PromptResponseArtifactDTO | ReasoningArtifactDTO
    rubric_version_id: str | None = Field(default=None, min_length=1)


class CompareSolutionsRequestDTO(ContractModel):
    workspace_id: str = Field(min_length=1)
    language: Language
    solution_a: str = Field(min_length=1, max_length=120_000)
    solution_b: str = Field(min_length=1, max_length=120_000)
    rubric_version_id: str | None = Field(default=None, min_length=1)


class BaseEvaluationResultDTO(ContractModel):
    id: str = Field(min_length=1)
    evaluation_type: EvaluationType
    score: Score
    confidence: ConfidenceScore
    evidence: list[Evidence]
    limitations: list[Limitation]
    detected_patterns: list[DetectedPattern]
    findings: list[Finding]
    breakdown: list[ScoreBreakdown]
    why: str = Field(min_length=1)
    engine_version: str = Field(min_length=1)
    rubric_version_id: str | None = Field(default=None, min_length=1)
    created_at: datetime


class ExportRequestDTO(ContractModel):
    workspace_id: str = Field(min_length=1)
    resource_type: Literal["evaluation", "dataset", "benchmark"]
    resource_id: str = Field(min_length=1)
    format: ExportFormat


class RubricScoreRequestDTO(ContractModel):
    workspace_id: str = Field(min_length=1)
    rubric: RubricVersionEntity
    result: BaseEvaluationResultDTO


class DatasetBuildRequestDTO(ContractModel):
    workspace_id: str = Field(min_length=1)
    topic: str = Field(min_length=2, max_length=160)
    language: Language = Language.python
    count: int = Field(default=5, ge=1, le=25)
    difficulty: Difficulty = Difficulty.mixed
    rubric_version_id: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list, max_length=20)


class DatasetBuildResultDTO(ContractModel):
    result: BaseEvaluationResultDTO
    items: list[DatasetItemEntity]
    exports: dict[ExportFormat, str]


class BenchmarkSummaryDTO(ContractModel):
    workspace_id: str = Field(min_length=1)
    evaluation_count: int = Field(ge=0)
    average_score: Score
    average_confidence: ConfidenceScore
    failure_categories: dict[str, int]
    language_distribution: dict[str, int]
    evaluation_type_distribution: dict[str, int]
    score_bands: dict[str, int]
    latency_p95_ms: int = Field(ge=0)
    generated_at: datetime


class ApiErrorDTO(ContractModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    request_id: str = Field(min_length=1)

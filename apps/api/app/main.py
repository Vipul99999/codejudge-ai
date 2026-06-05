from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analysis.bug_detector import detect_bugs
from app.analysis.code_analyzer import analyze_code
from app.analysis.comparator import compare_solutions
from app.analysis.complexity import analyze_complexity
from app.analysis.dataset import build_dataset
from app.analysis.llm_evaluator import evaluate_llm_response
from app.analysis.reasoning import review_reasoning
from app.analysis.rubric import score_rubric
from app.analysis.test_cases import generate_test_cases
from app.models import (
    BenchmarkEvent,
    BenchmarkSummary,
    BugDetectorResponse,
    CodeAnalysisResponse,
    CodeRequest,
    CompareRequest,
    ComparisonResponse,
    ComplexityResponse,
    DatasetRequest,
    DatasetResponse,
    LlmEvaluationRequest,
    LlmEvaluationResponse,
    ReasoningRequest,
    ReasoningResponse,
    RubricRequest,
    RubricResponse,
    TestCaseResponse,
)
from app.storage import benchmark_store

app = FastAPI(
    title="CodeJudge AI API",
    version="1.0.0",
    description=(
        "Deterministic static analysis APIs for code, reasoning, rubrics, "
        "and LLM-code evaluation."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def record(
    module: str,
    score: int,
    request: CodeRequest | None = None,
    bug_categories: list[str] | None = None,
    complexity: str | None = None,
) -> None:
    benchmark_store.add(
        BenchmarkEvent(
            module=module,
            score=score,
            language=request.language if request else None,
            bug_categories=bug_categories or [],
            complexity=complexity,
        )
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "static-analysis-only"}


@app.post("/api/analyze", response_model=CodeAnalysisResponse)
def analyze_endpoint(request: CodeRequest) -> CodeAnalysisResponse:
    response = analyze_code(request)
    record("Code Analyzer", response.overall_score, request)
    return response


@app.post("/api/bugs", response_model=BugDetectorResponse)
def bugs_endpoint(request: CodeRequest) -> BugDetectorResponse:
    response = detect_bugs(request)
    severity_score = max(0, 100 - len(response.findings) * 12)
    record(
        "Bug Detector", severity_score, request, [finding.category for finding in response.findings]
    )
    return response


@app.post("/api/test-cases", response_model=TestCaseResponse)
def test_cases_endpoint(request: CodeRequest) -> TestCaseResponse:
    response = generate_test_cases(request)
    record("Test Case Generator", 82, request)
    return response


@app.post("/api/complexity", response_model=ComplexityResponse)
def complexity_endpoint(request: CodeRequest) -> ComplexityResponse:
    response = analyze_complexity(request)
    record(
        "Complexity Analyzer",
        response.confidence_score,
        request,
        complexity=response.time_complexity,
    )
    return response


@app.post("/api/compare", response_model=ComparisonResponse)
def compare_endpoint(request: CompareRequest) -> ComparisonResponse:
    response = compare_solutions(request)
    record("Solution Comparator", max(response.solution_a_score, response.solution_b_score))
    return response


@app.post("/api/llm-evaluate", response_model=LlmEvaluationResponse)
def llm_endpoint(request: LlmEvaluationRequest) -> LlmEvaluationResponse:
    response = evaluate_llm_response(request)
    record("LLM Code Evaluator", response.overall_score)
    return response


@app.post("/api/reasoning", response_model=ReasoningResponse)
def reasoning_endpoint(request: ReasoningRequest) -> ReasoningResponse:
    response = review_reasoning(request)
    record("Reasoning Reviewer", response.score)
    return response


@app.post("/api/dataset", response_model=DatasetResponse)
def dataset_endpoint(request: DatasetRequest) -> DatasetResponse:
    response = build_dataset(request)
    record("Dataset Builder", 86)
    return response


@app.post("/api/rubric", response_model=RubricResponse)
def rubric_endpoint(request: RubricRequest) -> RubricResponse:
    response = score_rubric(request)
    record("Rubric Engine", round(response.weighted_score))
    return response


@app.get("/api/benchmarks", response_model=BenchmarkSummary)
def benchmark_endpoint() -> BenchmarkSummary:
    return benchmark_store.summary()

from __future__ import annotations

from fastapi import FastAPI, HTTPException
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
from app.contracts import (
    AnalysisRequestDTO,
    BaseEvaluationResultDTO,
    BenchmarkSummaryDTO,
    CodeArtifactDTO,
    CompareSolutionsRequestDTO,
    DatasetBuildRequestDTO,
    DatasetBuildResultDTO,
    EvaluationType,
    Language,
    PromptResponseArtifactDTO,
    ReasoningArtifactDTO,
    RubricScoreRequestDTO,
)
from app.engine.benchmark import Timer, benchmark_engine
from app.engine.bug_detection import detect_bug_risks
from app.engine.comparison import compare_solutions_contract
from app.engine.complexity import analyze_complexity_contract
from app.engine.dataset import build_dataset_contract
from app.engine.rubric import apply_rubric
from app.engine.static_analysis import analyze_static
from app.engine.test_generation import generate_test_plan
from app.engine.text_evaluation import evaluate_ai_response_contract, evaluate_reasoning_contract
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


def require_code_artifact(request: AnalysisRequestDTO) -> CodeArtifactDTO:
    if not isinstance(request.artifact, CodeArtifactDTO):
        raise HTTPException(status_code=422, detail="This analysis route requires a code artifact.")
    return request.artifact


def require_prompt_response_artifact(request: AnalysisRequestDTO) -> PromptResponseArtifactDTO:
    if not isinstance(request.artifact, PromptResponseArtifactDTO):
        raise HTTPException(
            status_code=422,
            detail="This analysis route requires a prompt-response artifact.",
        )
    return request.artifact


def require_reasoning_artifact(request: AnalysisRequestDTO) -> ReasoningArtifactDTO:
    if not isinstance(request.artifact, ReasoningArtifactDTO):
        raise HTTPException(
            status_code=422, detail="This analysis route requires a reasoning artifact."
        )
    return request.artifact


def record_contract_result(
    workspace_id: str,
    result: BaseEvaluationResultDTO,
    timer: Timer,
    language: Language | None = None,
) -> BaseEvaluationResultDTO:
    benchmark_engine.record(workspace_id, result, timer.elapsed_ms(), language=language)
    return result


@app.post("/api/analysis/code-review", response_model=BaseEvaluationResultDTO)
def code_review_contract_endpoint(request: AnalysisRequestDTO) -> BaseEvaluationResultDTO:
    if request.evaluation_type != EvaluationType.code_review:
        raise HTTPException(status_code=422, detail="evaluation_type must be code_review.")
    timer = Timer()
    artifact = require_code_artifact(request)
    result = analyze_static(artifact, rubric_version_id=request.rubric_version_id)
    return record_contract_result(request.workspace_id, result, timer, artifact.language)


@app.post("/api/analysis/bug-risk", response_model=BaseEvaluationResultDTO)
def bug_risk_contract_endpoint(request: AnalysisRequestDTO) -> BaseEvaluationResultDTO:
    if request.evaluation_type != EvaluationType.bug_risk:
        raise HTTPException(status_code=422, detail="evaluation_type must be bug_risk.")
    timer = Timer()
    artifact = require_code_artifact(request)
    result = detect_bug_risks(artifact)
    return record_contract_result(request.workspace_id, result, timer, artifact.language)


@app.post("/api/analysis/test-generation", response_model=BaseEvaluationResultDTO)
def test_generation_contract_endpoint(request: AnalysisRequestDTO) -> BaseEvaluationResultDTO:
    if request.evaluation_type != EvaluationType.test_generation:
        raise HTTPException(status_code=422, detail="evaluation_type must be test_generation.")
    timer = Timer()
    artifact = require_code_artifact(request)
    result, _exports = generate_test_plan(artifact)
    return record_contract_result(request.workspace_id, result, timer, artifact.language)


@app.post("/api/analysis/complexity", response_model=BaseEvaluationResultDTO)
def complexity_contract_endpoint(request: AnalysisRequestDTO) -> BaseEvaluationResultDTO:
    if request.evaluation_type != EvaluationType.complexity:
        raise HTTPException(status_code=422, detail="evaluation_type must be complexity.")
    timer = Timer()
    artifact = require_code_artifact(request)
    result = analyze_complexity_contract(artifact)
    return record_contract_result(request.workspace_id, result, timer, artifact.language)


@app.post("/api/analysis/compare", response_model=BaseEvaluationResultDTO)
def compare_contract_endpoint(request: CompareSolutionsRequestDTO) -> BaseEvaluationResultDTO:
    timer = Timer()
    result = compare_solutions_contract(request)
    return record_contract_result(request.workspace_id, result, timer, request.language)


@app.post("/api/analysis/ai-response", response_model=BaseEvaluationResultDTO)
def ai_response_contract_endpoint(request: AnalysisRequestDTO) -> BaseEvaluationResultDTO:
    if request.evaluation_type != EvaluationType.ai_response:
        raise HTTPException(status_code=422, detail="evaluation_type must be ai_response.")
    timer = Timer()
    artifact = require_prompt_response_artifact(request)
    result = evaluate_ai_response_contract(artifact)
    return record_contract_result(request.workspace_id, result, timer, artifact.language)


@app.post("/api/analysis/reasoning", response_model=BaseEvaluationResultDTO)
def reasoning_contract_endpoint(request: AnalysisRequestDTO) -> BaseEvaluationResultDTO:
    if request.evaluation_type != EvaluationType.reasoning:
        raise HTTPException(status_code=422, detail="evaluation_type must be reasoning.")
    timer = Timer()
    artifact = require_reasoning_artifact(request)
    result = evaluate_reasoning_contract(artifact)
    return record_contract_result(request.workspace_id, result, timer)


@app.post("/api/rubrics/score", response_model=BaseEvaluationResultDTO)
def rubric_score_contract_endpoint(request: RubricScoreRequestDTO) -> BaseEvaluationResultDTO:
    timer = Timer()
    result = apply_rubric(request.result, request.rubric)
    return record_contract_result(request.workspace_id, result, timer)


@app.post("/api/datasets/build", response_model=DatasetBuildResultDTO)
def dataset_build_contract_endpoint(request: DatasetBuildRequestDTO) -> DatasetBuildResultDTO:
    timer = Timer()
    result = build_dataset_contract(request)
    benchmark_engine.record(
        request.workspace_id,
        result.result,
        timer.elapsed_ms(),
        language=request.language,
    )
    return result


@app.get("/api/benchmarks", response_model=BenchmarkSummaryDTO)
def benchmark_contract_endpoint(workspace_id: str = "workspace-default") -> BenchmarkSummaryDTO:
    return benchmark_engine.summary(workspace_id)


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


@app.get("/api/benchmarks/legacy", response_model=BenchmarkSummary)
def benchmark_endpoint() -> BenchmarkSummary:
    return benchmark_store.summary()

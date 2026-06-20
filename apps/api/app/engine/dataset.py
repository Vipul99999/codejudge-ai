from __future__ import annotations

from typing import Literal, cast

from app.contracts import (
    BaseEvaluationResultDTO,
    DatasetBuildRequestDTO,
    DatasetBuildResultDTO,
    DatasetItemEntity,
    DetectedPattern,
    EvaluationType,
    Evidence,
    ExportFormat,
    Limitation,
    ScoreBreakdown,
)
from app.engine.primitives import (
    build_result,
    checksum_text,
    serialize_csv,
    serialize_json,
    stable_id,
)

DIFFICULTY_SEQUENCE = ("easy", "medium", "hard")


def build_dataset_contract(request: DatasetBuildRequestDTO) -> DatasetBuildResultDTO:
    tags = request.tags or [
        request.topic.lower().replace(" ", "-"),
        "static-analysis",
        "ai-evaluation",
    ]
    items: list[DatasetItemEntity] = []
    evidence: list[Evidence] = []

    for index in range(request.count):
        difficulty = (
            DIFFICULTY_SEQUENCE[index % len(DIFFICULTY_SEQUENCE)]
            if request.difficulty.value == "mixed"
            else request.difficulty.value
        )
        item_seed = checksum_text(f"{request.topic}|{request.language.value}|{index}")[:10]
        evidence_item = Evidence(
            id=stable_id("ev", "dataset.seed", request.topic, index),
            kind="metric",
            message=f"Dataset item {index + 1} is derived from stable seed {item_seed}.",
            rule_id="dataset.seed",
            metric_name="stable_seed",
            metric_value=item_seed,
        )
        evidence.append(evidence_item)
        items.append(
            DatasetItemEntity(
                id=stable_id("dataset-item", request.workspace_id, request.topic, index),
                problem=(
                    f"{request.topic}: evaluate a {request.language.value} solution for "
                    "correctness, complexity, edge coverage, and maintainability."
                ),
                solution=(
                    "Reference evaluator note: inspect invariants, boundary behavior, "
                    "control-flow complexity, and static bug risks without executing the code."
                ),
                rubric_version_id=request.rubric_version_id,
                difficulty=cast(Literal["easy", "medium", "hard"], difficulty),
                tags=tags,
            )
        )

    rows: list[dict[str, object]] = [
        {
            "id": item.id,
            "problem": item.problem,
            "solution": item.solution,
            "rubric_version_id": item.rubric_version_id,
            "difficulty": item.difficulty,
            "tags": "|".join(item.tags),
        }
        for item in items
    ]
    exports = {
        ExportFormat.json: serialize_json([item.model_dump() for item in items]),
        ExportFormat.csv: serialize_csv(rows),
        ExportFormat.parquet: serialize_json(
            {
                "format": "parquet-ready-json",
                "schema": list(rows[0].keys()) if rows else [],
                "rows": rows,
            }
        ),
    }

    score = min(100, 60 + request.count * 2 + len(tags) * 3)
    result: BaseEvaluationResultDTO = build_result(
        evaluation_type=EvaluationType.dataset_build,
        source_key=checksum_text(request.model_dump_json()),
        score=score,
        confidence=0.88,
        evidence=evidence,
        limitations=[
            Limitation(
                id="lim-dataset-static-template",
                scope="engine",
                message=(
                    "Dataset items are deterministic evaluator records; generated solutions "
                    "are evaluation notes, not executable answer keys."
                ),
            )
        ],
        patterns=[
            DetectedPattern(
                id=stable_id("pattern", "dataset.versioned", request.topic, request.count),
                name="Versionable deterministic dataset batch",
                category="dataset",
                confidence=0.9,
                evidence_ids=[item.id for item in evidence],
            )
        ],
        findings=[],
        breakdown=[
            ScoreBreakdown(
                category="dataset_structure",
                score=score,
                weight=0.45,
                why="Derived from item count, topic specificity, rubric linkage, and tags.",
                evidence_ids=[item.id for item in evidence],
            ),
            ScoreBreakdown(
                category="export_readiness",
                score=100,
                weight=0.35,
                why="JSON, CSV, and Parquet-ready exports are generated deterministically.",
                evidence_ids=[item.id for item in evidence],
            ),
            ScoreBreakdown(
                category="rubric_linkage",
                score=90,
                weight=0.2,
                why="Every dataset item carries the requested rubric version id.",
                evidence_ids=[item.id for item in evidence],
            ),
        ],
        why=(
            "Dataset score reflects deterministic generation coverage, export readiness, "
            "and rubric linkage."
        ),
        rubric_version_id=request.rubric_version_id,
    )
    return DatasetBuildResultDTO(result=result, items=items, exports=exports)

from __future__ import annotations

import json

from app.analysis.common import LIMITATIONS, csv_escape, stable_hash_score
from app.models import Confidence, DatasetItem, DatasetRequest, DatasetResponse, TestCase

DIFFICULTIES = ["easy", "medium", "hard"]


def build_dataset(request: DatasetRequest) -> DatasetResponse:
    tags = request.tags or [
        request.topic.lower().replace(" ", "-"),
        "static-analysis",
        "evaluation",
    ]
    items: list[DatasetItem] = []
    for index in range(request.count):
        if request.difficulty == "mixed":
            difficulty = DIFFICULTIES[index % len(DIFFICULTIES)]
        else:
            difficulty = request.difficulty
        seed = stable_hash_score(f"{request.topic}-{index}", 10, 99)
        problem = (
            f"{request.topic}: evaluate candidate solution variant {index + 1} "
            "and identify correctness, complexity, and edge-case risks."
        )
        solution = (
            f"Reference evaluation note {seed}: inspect invariants, boundary behavior, "
            "and complexity. "
            f"Use {request.language.value} syntax expectations without executing the code."
        )
        cases = [
            TestCase(
                case_type="normal",
                input=f"case-{index + 1}: representative input",
                expected_output="accepted baseline behavior",
                reason="Checks normal behavior.",
            ),
            TestCase(
                case_type="edge",
                input="empty or minimum-sized input",
                expected_output="graceful boundary behavior",
                reason="Checks missing boundary handling.",
            ),
            TestCase(
                case_type="stress",
                input="maximum constraint input",
                expected_output="same semantics within estimated complexity",
                reason="Checks scalability assumptions.",
            ),
        ]
        items.append(
            DatasetItem(
                problem=problem,
                solution=solution,
                test_cases=cases,
                difficulty=difficulty,
                tags=tags,
            )
        )

    json_export = json.dumps([item.model_dump() for item in items], indent=2)
    csv_lines = ["problem,solution,difficulty,tags"]
    for item in items:
        csv_lines.append(
            ",".join(
                [
                    csv_escape(item.problem),
                    csv_escape(item.solution),
                    item.difficulty,
                    csv_escape("|".join(item.tags)),
                ]
            )
        )

    return DatasetResponse(
        items=items,
        export={"json": json_export, "csv": "\n".join(csv_lines)},
        confidence=Confidence.high,
        reason="Deterministic template generation with stable seeded variation",
        limitations=LIMITATIONS,
    )

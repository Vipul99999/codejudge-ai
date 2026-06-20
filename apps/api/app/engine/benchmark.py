from __future__ import annotations

from collections import Counter, deque
from threading import Lock
from time import perf_counter

from app.contracts import (
    BaseEvaluationResultDTO,
    BenchmarkEventEntity,
    BenchmarkSummaryDTO,
    Language,
)
from app.engine.primitives import now_utc, stable_id


class BenchmarkEngine:
    def __init__(self, max_events: int = 2_000) -> None:
        self._events: deque[BenchmarkEventEntity] = deque(maxlen=max_events)
        self._lock = Lock()

    def record(
        self,
        workspace_id: str,
        result: BaseEvaluationResultDTO,
        latency_ms: int,
        language: Language | None = None,
    ) -> BenchmarkEventEntity:
        event = BenchmarkEventEntity(
            id=stable_id("benchmark", workspace_id, result.id, len(self._events)),
            evaluation_id=result.id,
            workspace_id=workspace_id,
            evaluation_type=result.evaluation_type,
            language=language,
            score=result.score,
            confidence=result.confidence,
            latency_ms=latency_ms,
            failure_categories=[finding.category for finding in result.findings],
            engine_version=result.engine_version,
            rubric_version_id=result.rubric_version_id,
            occurred_at=now_utc(),
        )
        with self._lock:
            self._events.append(event)
        return event

    def summary(self, workspace_id: str) -> BenchmarkSummaryDTO:
        with self._lock:
            events = [event for event in self._events if event.workspace_id == workspace_id]
        if not events:
            return BenchmarkSummaryDTO(
                workspace_id=workspace_id,
                evaluation_count=0,
                average_score=0,
                average_confidence=0,
                failure_categories={},
                language_distribution={},
                evaluation_type_distribution={},
                score_bands={"0-49": 0, "50-69": 0, "70-84": 0, "85-100": 0},
                latency_p95_ms=0,
                generated_at=now_utc(),
            )

        score_bands = Counter(score_band(event.score) for event in events)
        latencies = sorted(event.latency_ms for event in events)
        p95_index = min(len(latencies) - 1, int(len(latencies) * 0.95))

        return BenchmarkSummaryDTO(
            workspace_id=workspace_id,
            evaluation_count=len(events),
            average_score=round(sum(event.score for event in events) / len(events), 2),
            average_confidence=round(sum(event.confidence for event in events) / len(events), 3),
            failure_categories=dict(
                Counter(category for event in events for category in event.failure_categories)
            ),
            language_distribution=dict(
                Counter(event.language.value for event in events if event.language)
            ),
            evaluation_type_distribution=dict(
                Counter(event.evaluation_type.value for event in events)
            ),
            score_bands={
                band: score_bands.get(band, 0) for band in ["0-49", "50-69", "70-84", "85-100"]
            },
            latency_p95_ms=latencies[p95_index],
            generated_at=now_utc(),
        )


def score_band(score: float) -> str:
    if score < 50:
        return "0-49"
    if score < 70:
        return "50-69"
    if score < 85:
        return "70-84"
    return "85-100"


class Timer:
    def __init__(self) -> None:
        self._start = perf_counter()

    def elapsed_ms(self) -> int:
        return round((perf_counter() - self._start) * 1_000)


benchmark_engine = BenchmarkEngine()

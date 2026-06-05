from __future__ import annotations

from collections import Counter, deque
from threading import Lock

from app.models import BenchmarkEvent, BenchmarkSummary


class BenchmarkStore:
    def __init__(self, max_events: int = 500) -> None:
        self._events: deque[BenchmarkEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def add(self, event: BenchmarkEvent) -> None:
        with self._lock:
            self._events.append(event)

    def summary(self) -> BenchmarkSummary:
        with self._lock:
            events = list(self._events)
        if not events:
            return BenchmarkSummary(
                evaluations_performed=0,
                average_score=0,
                common_bug_categories=[],
                complexity_distribution=[],
                module_distribution=[],
            )
        bugs = Counter(category for event in events for category in event.bug_categories)
        complexities = Counter(event.complexity for event in events if event.complexity)
        modules = Counter(event.module for event in events)
        return BenchmarkSummary(
            evaluations_performed=len(events),
            average_score=round(sum(event.score for event in events) / len(events), 2),
            common_bug_categories=[{key: value} for key, value in bugs.most_common(8)],
            complexity_distribution=[{key: value} for key, value in complexities.most_common()],
            module_distribution=[{key: value} for key, value in modules.most_common()],
        )


benchmark_store = BenchmarkStore()

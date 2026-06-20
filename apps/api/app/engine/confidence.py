from __future__ import annotations

from collections.abc import Sequence

from app.contracts import Evidence, Finding, Limitation, SupportTier
from app.engine.primitives import CodeMetrics, clamp_confidence


def confidence_from_metrics(
    metrics: CodeMetrics,
    evidence: Sequence[Evidence],
    findings: Sequence[Finding],
    limitations: Sequence[Limitation],
) -> tuple[float, list[str], list[str]]:
    drivers: list[str] = []
    reducers: list[str] = []
    confidence = 0.46

    if metrics.support_tier == SupportTier.tier_1 and metrics.parse_ok:
        confidence += 0.24
        drivers.append("Tier 1 parser support produced AST-backed metrics.")
    elif metrics.support_tier == SupportTier.tier_2:
        confidence += 0.14
        drivers.append("Tier 2 parser-style structural rules were available.")
    else:
        confidence += 0.06
        reducers.append("Language support is heuristic-only for this artifact.")

    if evidence:
        confidence += min(0.16, len(evidence) * 0.018)
        drivers.append(f"{len(evidence)} evidence item(s) support the result.")
    else:
        confidence -= 0.18
        reducers.append("No evidence was available for the result.")

    if metrics.non_empty_lines >= 8:
        confidence += 0.05
        drivers.append("Input has enough structure for static analysis.")
    else:
        confidence -= 0.08
        reducers.append("Very small inputs reduce evaluator confidence.")

    if metrics.parse_error:
        confidence -= 0.2
        reducers.append(metrics.parse_error)

    if limitations:
        confidence -= min(0.12, len(limitations) * 0.025)

    if findings and all(finding.evidence_ids for finding in findings):
        confidence += 0.04
        drivers.append("Findings are tied to explicit evidence IDs.")

    return clamp_confidence(confidence), drivers, reducers


def confidence_why(drivers: Sequence[str], reducers: Sequence[str]) -> str:
    driver_text = " ".join(drivers) if drivers else "No strong confidence drivers were present."
    reducer_text = " ".join(reducers) if reducers else "No major confidence reducers were present."
    return f"{driver_text} {reducer_text}"

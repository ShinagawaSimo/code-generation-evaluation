from typing import Any, Dict

from .models import MetricResult


def evaluate_specification_completeness(expansion_result: Dict[str, Any]) -> MetricResult:
    points = expansion_result.get("requirement_points", [])
    total_basic_count = sum(
        1
        for point in points
        if point.get("category") in {"basic_function", "implicit_function"}
    )
    covered_basic_count = sum(
        1
        for point in points
        if point.get("category") in {"basic_function", "implicit_function"}
        and point.get("is_explicit_in_original")
    )
    completeness_ratio = (
        covered_basic_count / total_basic_count if total_basic_count else 0.0
    )
    return MetricResult(
        name="specification_completeness",
        values={
            "covered_basic_requirement_count": covered_basic_count,
            "total_basic_requirement_count": total_basic_count,
            "completeness_ratio": completeness_ratio,
        },
    )

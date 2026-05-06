from typing import Any, Dict

from .models import MetricResult


def evaluate_specification_complexity(expansion_result: Dict[str, Any]) -> MetricResult:
    points = expansion_result["requirement_points"]
    visible_count = sum(1 for point in points if point["is_explicit_in_original"])
    implicit_total_count = sum(1 for point in points if point["category"] == "implicit_function")
    implicit_missing_count = sum(
        1
        for point in points
        if point["category"] == "implicit_function" and not point["is_explicit_in_original"]
    )
    total_complexity_count = visible_count + implicit_missing_count
    return MetricResult(
        values={
            "visible_requirement_point_count": visible_count,
            "implicit_function_total_count": implicit_total_count,
            "implicit_function_missing_count": implicit_missing_count,
            "total_complexity_count": total_complexity_count,
        },
    )

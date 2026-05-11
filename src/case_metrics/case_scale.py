from typing import Any, Dict

from .models import MetricResult
from .tokenizer import count_tokens


def evaluate_case_scale(
    original_requirement_text: str,
    expansion_result: Dict[str, Any],
    metric_config: Dict[str, Any],
) -> MetricResult:
    token_count = count_tokens(original_requirement_text, metric_config)
    points = expansion_result["requirement_points"]
    visible_count = sum(1 for point in points if point["is_explicit_in_original"])
    implicit_missing_count = sum(
        1 for point in points
        if point["category"] == "implicit_function" and not point["is_explicit_in_original"]
    )
    requirement_point_count = visible_count + implicit_missing_count
    return MetricResult(
        values={
            "token_count": token_count,
            "requirement_point_count": requirement_point_count,
        },
    )

import re
from typing import Any, Dict, List

from .models import MetricResult


EARS_PATTERNS = [
    re.compile(r"^\s*(当|如果|在.+状态下|若|一旦).+"),
    re.compile(r"^\s*(When|If|While|Where|Once).+", re.IGNORECASE),
    re.compile(r".+\s*(应|必须|shall|should)\s*.+", re.IGNORECASE),
]


def _matches_ears(text: str) -> bool:
    return any(pattern.search(text) for pattern in EARS_PATTERNS)


def evaluate_expression_format(expansion_result: Dict[str, Any]) -> MetricResult:
    points = expansion_result.get("requirement_points", [])
    explicit_points = [point for point in points if point.get("is_explicit_in_original")]
    matched_point_ids: List[str] = []
    unmatched_point_ids: List[str] = []
    for point in explicit_points:
        fragments = [str(text) for text in point.get("original_source_texts", []) if str(text).strip()]
        if fragments and any(_matches_ears(fragment) for fragment in fragments):
            matched_point_ids.append(str(point.get("point_id", "")))
        else:
            unmatched_point_ids.append(str(point.get("point_id", "")))
    explicit_requirement_point_count = len(explicit_points)
    ears_match_count = len(matched_point_ids)
    ears_ratio = ears_match_count / explicit_requirement_point_count if explicit_requirement_point_count else 0.0
    return MetricResult(
        name="expression_format",
        values={
            "explicit_requirement_point_count": explicit_requirement_point_count,
            "ears_match_count": ears_match_count,
            "ears_ratio": ears_ratio,
            "matched_point_ids": matched_point_ids,
            "unmatched_point_ids": unmatched_point_ids,
        },
    )

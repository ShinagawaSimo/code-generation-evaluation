import re
from typing import Any, Dict

from .models import MetricResult
from .tokenizer import count_tokens


def _count_numbered_items(text: str) -> int:
    matches = re.findall(r"(?:^|：|;|；|\n)\s*(\d+)[.、]", text)
    return len(matches)


def evaluate_case_scale(
    original_requirement_text: str,
    metric_config: Dict[str, Any],
) -> MetricResult:
    token_count = count_tokens(original_requirement_text, metric_config)
    requirement_point_count = _count_numbered_items(original_requirement_text)
    return MetricResult(
        values={
            "token_count": token_count,
            "requirement_point_count": requirement_point_count,
        },
    )

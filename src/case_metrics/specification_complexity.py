import re
from pathlib import Path
from typing import Any, Dict

from .models import MetricResult


def evaluate_specification_complexity(
    expansion_result: Dict[str, Any],
    cases_dir: str,
) -> MetricResult:
    task_id = str(expansion_result["task_id"])
    case_path = Path(cases_dir) / f"{task_id}.txt"
    complexity_rating = 1
    if case_path.exists():
        text = case_path.read_text(encoding="utf-8")
        match = re.search(r"Complexity:\s*(\d+)", text)
        if match:
            complexity_rating = max(1, min(5, int(match.group(1))))
    return MetricResult(
        values={
            "complexity_rating": complexity_rating,
        },
    )

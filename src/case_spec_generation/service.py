import json
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import CaseSpecRequest, CaseSpecResult, RequirementPoint
from .prompting import build_case_spec_input, get_case_spec_generation_prompt


def _extract_json_block(raw_output: str) -> str:
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model output does not contain a JSON object")
    return stripped[start : end + 1]


def _parse_requirement_points(items: List[Dict[str, Any]]) -> List[RequirementPoint]:
    points: List[RequirementPoint] = []
    for item in items:
        points.append(
            RequirementPoint(
                point_id=str(item["point_id"]),
                point_text=str(item["point_text"]).strip(),
                category=str(item["category"]),
                is_explicit_in_original=bool(item["is_explicit_in_original"]),
                original_source_texts=[
                    str(text).strip() for text in item["original_source_texts"]
                ],
            )
        )
    return points


def _build_original_covered_counts(points: List[RequirementPoint]) -> Dict[str, int]:
    counts: Dict[str, int] = {
        "basic_function": 0,
        "implicit_function": 0,
        "optional_function": 0,
        "basic_non_function": 0,
        "optional_non_function": 0,
    }
    for point in points:
        if point.is_explicit_in_original and point.category in counts:
            counts[point.category] += 1
    return counts


def generate_case_spec(
    request: CaseSpecRequest,
    api_config: Dict[str, Any],
    prompt_text: str | None = None,
) -> CaseSpecResult:
    prompt = prompt_text or get_case_spec_generation_prompt()
    user_input = build_case_spec_input(request)
    raw_output = call_model(api_config, prompt, user_input)
    parsed = json.loads(_extract_json_block(raw_output))
    requirement_points = _parse_requirement_points(parsed.get("requirement_points", []))
    summary = dict(parsed.get("summary", {}))
    summary.setdefault("original_covered_counts", _build_original_covered_counts(requirement_points))
    return CaseSpecResult(
        task_id=request.task_id,
        language=request.language,
        original_requirement_text=request.original_requirement_text,
        requirement_points=requirement_points,
        summary=summary,
    )

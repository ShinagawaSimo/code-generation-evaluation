import json
from typing import Any, Dict, List

from .models import RequirementExpansionRequest, RequirementExpansionResult, RequirementPoint
from .prompting import build_requirement_expansion_input, get_requirement_expansion_prompt
from shared.model_client import call_model


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
    for index, item in enumerate(items, start=1):
        points.append(
            RequirementPoint(
                point_id=str(item.get("point_id") or f"point_{index:03d}"),
                point_text=str(item.get("point_text", "")).strip(),
                category=str(item.get("category", "basic_function")),
                is_explicit_in_original=bool(item.get("is_explicit_in_original", False)),
                original_source_texts=[
                    str(text).strip() for text in item.get("original_source_texts", []) if str(text).strip()
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


def expand_requirement(
    request: RequirementExpansionRequest,
    api_config: Dict[str, Any],
    prompt_text: str | None = None,
) -> RequirementExpansionResult:
    prompt = prompt_text or get_requirement_expansion_prompt()
    user_input = build_requirement_expansion_input(request)
    raw_output = call_model(api_config, prompt, user_input)
    parsed = json.loads(_extract_json_block(raw_output))
    requirement_points = _parse_requirement_points(parsed.get("requirement_points", []))
    summary = dict(parsed.get("summary", {}))
    summary.setdefault("original_covered_counts", _build_original_covered_counts(requirement_points))
    return RequirementExpansionResult(
        task_id=request.task_id,
        language=request.language,
        original_requirement_text=request.original_requirement_text,
        expanded_requirement_text=str(parsed.get("expanded_requirement_text", "")).strip(),
        requirement_points=requirement_points,
        summary=summary,
        raw_response=raw_output,
    )

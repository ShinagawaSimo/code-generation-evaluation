import json
from pathlib import Path
from typing import Any, Dict

from .models import RequirementExpansionRequest


DEFAULT_PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "requirement_expansion_prompt.txt"
)


def _build_output_contract() -> Dict[str, Any]:
    return {
        "expanded_requirement_text": "string",
        "requirement_points": [
            {
                "point_id": "string",
                "point_text": "string",
                "category": "basic_function | implicit_function | optional_function | basic_non_function | optional_non_function",
                "is_explicit_in_original": "boolean",
                "original_source_texts": ["string"],
            }
        ],
        "summary": {
            "basic_function_count": "integer",
            "implicit_function_count": "integer",
            "optional_function_count": "integer",
            "basic_non_function_count": "integer",
            "optional_non_function_count": "integer",
            "original_covered_counts": {
                "basic_function": "integer",
                "implicit_function": "integer",
                "optional_function": "integer",
                "basic_non_function": "integer",
                "optional_non_function": "integer",
            },
        },
    }


def get_requirement_expansion_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def build_requirement_expansion_input(request: RequirementExpansionRequest) -> str:
    payload = request.to_prompt_payload()
    payload["classification_guide"] = {
        "basic_function": "Must-have function explicitly required by task or indispensable for core task completion.",
        "implicit_function": "Must-have function or handling logic even if original text does not say it directly, such as invalid input, boundary cases, or safe state transitions.",
        "optional_function": "Nice-to-have feature extension or interaction convenience, not required for core correctness.",
        "basic_non_function": "Must-have non-functional constraint, such as hard performance, safety, or environment limits.",
        "optional_non_function": "Non-functional preference or soft constraint, such as style or extra performance target.",
    }
    payload["output_contract"] = _build_output_contract()
    payload["response_rules"] = [
        "Return JSON only.",
        "Do not wrap JSON in markdown code fences.",
        "Requirement points must cover whole expanded requirement text.",
        "Each requirement point must map to exactly one minimal idea.",
        "When original text semantically reflects a point, set is_explicit_in_original to true and extract every relevant exact text span into original_source_texts.",
        "When original text does not reflect a point, original_source_texts must be an empty array.",
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)

import json
from pathlib import Path
from typing import Any, Dict

from .models import CaseSpecRequest


DEFAULT_PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "case_spec_generation_prompt.txt"
)


def _build_output_contract() -> Dict[str, Any]:
    return {
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


def get_case_spec_generation_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def build_case_spec_input(request: CaseSpecRequest) -> str:
    payload = request.to_prompt_payload()
    payload["output_contract"] = _build_output_contract()
    payload["response_reminder"] = "Return JSON only, no markdown."
    return json.dumps(payload, ensure_ascii=False, indent=2)

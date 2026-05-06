import json
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import ReferenceCodeResult, ReferenceImplementation
from .prompting import build_reference_code_input, load_reference_code_prompt


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


def _parse_implementations(items: List[Dict[str, Any]]) -> List[ReferenceImplementation]:
    impls: List[ReferenceImplementation] = []
    for item in items:
        impls.append(
            ReferenceImplementation(
                code_text=str(item["code_text"]),
                implemented_interface=dict(item["implemented_interface"]),
                approach_metadata=dict(item["approach_metadata"]),
            )
        )
    return impls


def generate_reference_code(
    task_id: str,
    language: str,
    original_requirement_text: str,
    api_config: Dict[str, Any],
    prompt_text: str | None = None,
) -> ReferenceCodeResult:
    prompt = prompt_text or load_reference_code_prompt()
    user_input = build_reference_code_input(
        task_id=task_id,
        language=language,
        original_requirement_text=original_requirement_text,
    )
    raw_output = call_model(api_config, prompt, user_input)
    parsed = json.loads(_extract_json_block(raw_output))
    implementations = _parse_implementations(parsed["implementations"])
    print(
        f"[reference_code_generation] task={task_id} "
        f"approaches={len(parsed['approach_enumeration'])} "
        f"implementations={len(implementations)}"
    )
    return ReferenceCodeResult(
        task_id=task_id,
        language=language,
        reference_implementations=implementations,
    )

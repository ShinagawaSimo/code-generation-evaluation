import json
from pathlib import Path
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import RequirementPointTestSpec, TestGenerationResult
from .prompting import build_test_generation_input, load_test_generation_prompt
from .renderer import render_point_artifacts, write_point_artifacts


def _extract_json_block(raw_output: str) -> str:
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()
    return stripped


def _parse_model_json(raw_output: str) -> Dict[str, Any]:
    text = _extract_json_block(raw_output)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model output does not contain a JSON object")
    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON is not an object")
        return parsed
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Failed to parse model JSON. Hint: use strict JSON literals only (null/true/false, not None/True/False). "
            f"Error: {error}"
        ) from error


def _require_dict(value: Any, field_name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be object")
    return value


def _require_list(value: Any, field_name: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be array")
    return value


def _validate_function_call_schema(parsed: Dict[str, Any]) -> None:
    target_signature = _require_dict(parsed["target_signature"], "target_signature")
    function_contract = _require_dict(parsed["function_contract"], "function_contract")
    assertions = _require_list(parsed["assertions"], "assertions")
    if not str(target_signature["entry_name"]).strip():
        raise ValueError("target_signature.entry_name must be non-empty for function_call")
    parameters = _require_list(target_signature["parameters"], "target_signature.parameters")
    for index, parameter in enumerate(parameters):
        if not isinstance(parameter, dict):
            raise ValueError(f"target_signature.parameters[{index}] must be object")
    _require_list(function_contract["parameter_order"], "function_contract.parameter_order")
    _require_list(function_contract["notes"], "function_contract.notes")
    for index, assertion in enumerate(assertions):
        if not isinstance(assertion, dict):
            raise ValueError(f"assertions[{index}] must be object")
        call = _require_dict(assertion["call"], f"assertions[{index}].call")
        expectation = _require_dict(assertion["expectation"], f"assertions[{index}].expectation")
        _require_list(call["args"], f"assertions[{index}].call.args")
        if not isinstance(call.get("kwargs", {}), dict):
            raise ValueError(f"assertions[{index}].call.kwargs must be object")
        expectation_kind = str(expectation["kind"])
        if expectation_kind not in {
            "equals",
            "raises",
            "input_unchanged",
            "new_object",
            "multiset_equals",
            "type_hints",
            "max_runtime_seconds",
        }:
            raise ValueError(f"unsupported expectation.kind: {expectation_kind}")
def _validate_program_io_schema(parsed: Dict[str, Any]) -> None:
    io_cases = _require_list(parsed["io_cases"], "io_cases")
    for index, case in enumerate(io_cases):
        if not isinstance(case, dict):
            raise ValueError(f"io_cases[{index}] must be object")
        if not isinstance(case["input_text"], str):
            raise ValueError(f"io_cases[{index}].input_text must be string")
        if not isinstance(case["expected_output_text"], str):
            raise ValueError(f"io_cases[{index}].expected_output_text must be string")


def _validate_test_spec(parsed: Dict[str, Any], point: Dict[str, Any]) -> None:
    expected_point_id = str(point["point_id"])
    actual_point_id = str(parsed["point_id"])
    if expected_point_id and actual_point_id and expected_point_id != actual_point_id:
        raise ValueError(f"point_id mismatch: expected={expected_point_id} actual={actual_point_id}")
    execution_mode = str(parsed["execution_mode"])
    if execution_mode not in {"program_io", "function_call", "gui_or_server"}:
        raise ValueError(f"unsupported execution_mode: {execution_mode}")
    if execution_mode == "function_call":
        _validate_function_call_schema(parsed)
    elif execution_mode == "program_io":
        _validate_program_io_schema(parsed)


def _build_point_spec(parsed: Dict[str, Any], point: Dict[str, Any], language: str) -> RequirementPointTestSpec:
    _validate_test_spec(parsed, point)
    return RequirementPointTestSpec(
        point_id=str(parsed["point_id"]),
        point_text=str(point["point_text"]),
        category=str(point["category"]),
        test_kind=str(parsed["test_kind"]),
        execution_mode=str(parsed["execution_mode"]),
        language=str(parsed["language"]),
        suggested_entry_name=str(parsed.get("suggested_entry_name", "")),
        target_signature=dict(parsed.get("target_signature") or {}),
        function_contract=dict(parsed.get("function_contract") or {}),
        io_cases=list(parsed.get("io_cases", [])),
        assertions=list(parsed.get("assertions", [])),
        environment=dict(parsed.get("environment") or {}),
        artifact_hints=dict(parsed.get("artifact_hints") or {}),
        test_skeleton=dict(parsed.get("test_skeleton") or {}),
    )


def generate_tests_for_case(
    expansion_result: Dict[str, Any],
    api_config: Dict[str, Any],
    generation_config: Dict[str, Any],
    output_dir: str,
) -> TestGenerationResult:
    prompt = load_test_generation_prompt(generation_config.get("prompt_path"))
    task_id = str(expansion_result["task_id"])
    language = str(expansion_result["language"])
    original_requirement_text = str(expansion_result["original_requirement_text"])
    point_specs: List[RequirementPointTestSpec] = []
    generated_files: List[str] = []
    raw_output_dir = Path(output_dir) / "_raw_model_outputs"
    raw_output_dir.mkdir(parents=True, exist_ok=True)

    points = list(expansion_result["requirement_points"])
    total_points = len(points)
    print(f"[test_generation] task={task_id} points={total_points} language={language}")
    for point_index, point in enumerate(points, start=1):
        point_id = str(point["point_id"])
        print(f"[test_generation] point {point_index}/{total_points} id={point_id}")
        user_input = build_test_generation_input(
            task_id=task_id,
            language=language,
            original_requirement_text=original_requirement_text,
            requirement_point=point,
        )
        raw_output = call_model(api_config, prompt, user_input)
        raw_output_path = raw_output_dir / f"{point_id}.txt"
        raw_output_path.write_text(raw_output, encoding="utf-8")
        try:
            parsed = _parse_model_json(raw_output)
        except Exception as error:  # noqa: BLE001
            raise ValueError(
                f"Failed to parse test-generation JSON for task={task_id} point={point_id}. "
                f"Raw model output saved at: {raw_output_path}. Error: {error}"
            ) from error
        point_spec = _build_point_spec(parsed, point, language)
        point_specs.append(point_spec)
        artifacts = render_point_artifacts(point_spec)
        generated_files.extend(write_point_artifacts(output_dir, point_spec.point_id, artifacts))
        print(f"[test_generation] point done id={point_spec.point_id} artifacts={len(artifacts)}")

    return TestGenerationResult(
        task_id=task_id,
        language=language,
        point_specs=point_specs,
        generated_files=generated_files,
    )

import json
from pathlib import Path
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import TestGenerationResult
from .prompting import (
    build_mode_analysis_input,
    build_test_generation_input,
    load_mode_analysis_prompt,
    load_test_generation_prompt,
)
from .renderers import render_tests


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
            f"Failed to parse model JSON. Hint: use strict JSON literals only. Error: {error}"
        ) from error


def _validate_mode_analysis(parsed: Dict[str, Any]) -> List[Dict[str, str]]:
    modes = list(parsed.get("test_modes", []))
    for entry in modes:
        mode = str(entry.get("mode", ""))
        if mode not in {"function_call", "program_io"}:
            raise ValueError(f"Unsupported test mode: {mode}")
    return modes


def _validate_test_spec(parsed: Dict[str, Any]) -> Dict[str, Any]:
    execution_mode = str(parsed.get("execution_mode", ""))
    if execution_mode not in {"function_call", "program_io"}:
        raise ValueError(f"Unsupported execution_mode: {execution_mode}")
    language = str(parsed.get("language", ""))
    tests = list(parsed.get("tests", []))
    if not tests:
        raise ValueError("tests must be a non-empty array")
    for test in tests:
        if not isinstance(test, dict):
            raise ValueError("Each test must be an object")
        if not str(test.get("test_id", "")).strip():
            raise ValueError("Each test must have a non-empty test_id")
        if execution_mode == "function_call":
            call_data = test.get("call", {})
            if not isinstance(call_data, dict):
                raise ValueError("function_call test must have a call object")
            if not isinstance(call_data.get("args", []), list):
                raise ValueError("call.args must be an array")
            expectation = test.get("expectation", {})
            if not isinstance(expectation, dict):
                raise ValueError("function_call test must have an expectation object")
            kind = str(expectation.get("kind", ""))
            if kind not in {"equals", "raises", "input_unchanged", "new_object", "type_hints", "max_runtime_seconds", "multiset_equals"}:
                raise ValueError(f"Unsupported expectation.kind: {kind}")
        elif execution_mode == "program_io":
            io_case = test.get("io_case", {})
            if not isinstance(io_case, dict):
                raise ValueError("program_io test must have io_case object")
            if not isinstance(io_case.get("input_text"), str):
                raise ValueError("io_case.input_text must be a string")
            if not isinstance(io_case.get("expected_output_text"), str):
                raise ValueError("io_case.expected_output_text must be a string")
    return {
        "execution_mode": execution_mode,
        "language": language,
        "target_signature": dict(parsed.get("target_signature") or {}),
        "tests": tests,
    }


def generate_tests_for_case(
    task_id: str,
    original_requirement_text: str,
    language: str,
    api_config: Dict[str, Any],
    generation_config: Dict[str, Any],
    tests_output_dir: str,
) -> TestGenerationResult:
    mode_analysis_prompt = load_mode_analysis_prompt(
        generation_config.get("mode_analysis_prompt_path")
    )
    test_generation_prompt = load_test_generation_prompt(
        generation_config.get("test_generation_prompt_path")
    )
    print(f"[test_generation] task={task_id} language={language} phase=1 mode_analysis")
    mode_input = build_mode_analysis_input(task_id, language, original_requirement_text)
    mode_raw_output, *_ = call_model(api_config, mode_analysis_prompt, mode_input)
    mode_parsed = _parse_model_json(mode_raw_output)
    test_modes = _validate_mode_analysis(mode_parsed)
    print(f"[test_generation] task={task_id} modes={[m['mode'] for m in test_modes]}")

    output_paths: List[str] = []
    for mode_entry in test_modes:
        mode = str(mode_entry["mode"])
        reasoning = str(mode_entry.get("reasoning", ""))
        print(f"[test_generation] task={task_id} phase=2 mode={mode}")
        spec_input = build_test_generation_input(
            task_id, language, original_requirement_text, mode, reasoning,
        )
        spec_raw_output, *_ = call_model(api_config, test_generation_prompt, spec_input)
        spec_parsed = _parse_model_json(spec_raw_output)
        spec = _validate_test_spec(spec_parsed)
        mode_output_dir = str(Path(tests_output_dir) / mode)
        mode_paths = render_tests(spec, mode_output_dir)
        output_paths.extend(mode_paths)
        print(f"[test_generation] task={task_id} mode={mode} files={len(mode_paths)}")

    return TestGenerationResult(
        task_id=task_id,
        language=language,
        generated_files=output_paths,
    )

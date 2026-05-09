import ast
import json
from pathlib import Path
import re
from typing import Any, Dict

from shared.model_client import call_model

from .models import CodeGenerationRequest, CodeGenerationResult
from .prompting import (
    build_code_filename,
    build_code_generation_input,
    build_self_review_input,
    load_code_generation_prompt,
)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_json_payload(raw_output: str) -> Dict[str, Any]:
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model output does not contain a JSON object")
    parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Model output JSON must be an object")
    return parsed


def _extract_code_and_interface(raw_output: str) -> tuple[str, Dict[str, Any]]:
    parsed = _extract_json_payload(raw_output)
    code_text = _strip_code_fence(str(parsed.get("code_text", "")))
    implemented_interface = dict(parsed.get("implemented_interface", {}))
    if not code_text:
        raise ValueError("Model output missing code_text")
    return code_text, implemented_interface


def _validate_python_function_interface(code_text: str, implemented_interface: Dict[str, Any]) -> tuple[bool, str]:
    entry_name = str(implemented_interface.get("entry_name", "")).strip()
    if not entry_name:
        return False, "implemented_interface.entry_name is empty"
    try:
        tree = ast.parse(code_text)
    except SyntaxError as error:
        return False, f"python_syntax_error: {error}"
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    target = next((node for node in functions if node.name == entry_name), None)
    if target is None:
        return False, f"entry function not found in code: {entry_name}"
    declared_parameters = [
        item for item in implemented_interface.get("parameters", []) if isinstance(item, dict)
    ]
    if declared_parameters:
        actual_parameter_count = len(target.args.args)
        if actual_parameter_count != len(declared_parameters):
            return (
                False,
                f"parameter count mismatch for {entry_name}: "
                f"declared={len(declared_parameters)} actual={actual_parameter_count}",
            )
    return True, ""


def _validate_generic_function_interface(code_text: str, implemented_interface: Dict[str, Any]) -> tuple[bool, str]:
    entry_name = str(implemented_interface.get("entry_name", "")).strip()
    if not entry_name:
        return False, "implemented_interface.entry_name is empty"
    if re.search(rf"\b{re.escape(entry_name)}\s*\(", code_text):
        return True, ""
    return False, f"entry symbol not found in code: {entry_name}"


def _validate_implemented_interface(language: str, code_text: str, implemented_interface: Dict[str, Any]) -> tuple[bool, str]:
    interface_type = str(implemented_interface.get("interface_type", "")).strip()
    if interface_type not in {"function_call", "program_io", "gui_or_server"}:
        return False, f"unsupported interface_type: {interface_type}"
    if interface_type != "function_call":
        return True, ""
    if language == "python":
        return _validate_python_function_interface(code_text, implemented_interface)
    return _validate_generic_function_interface(code_text, implemented_interface)


def generate_code(
    request: CodeGenerationRequest,
    api_config: Dict[str, Any],
    generation_config: Dict[str, Any],
    code_output_dir: str,
    raw_output_dir: str,
) -> CodeGenerationResult:
    prompt = load_code_generation_prompt(generation_config.get("prompt_path"))
    max_rounds = int(generation_config.get("max_rounds", 1))
    inference_time_seconds = 0.0
    prompt_tokens = 0
    completion_tokens = 0

    raw_output, inf_time, pt, ct = call_model(
        api_config, prompt, build_code_generation_input(request)
    )
    inference_time_seconds += inf_time
    prompt_tokens += pt
    completion_tokens += ct
    code_text, implemented_interface = _extract_code_and_interface(raw_output)
    rounds_used = 1

    while rounds_used < max_rounds:
        rounds_used += 1
        raw_output, inf_time, pt, ct = call_model(
            api_config, prompt, build_self_review_input(request, code_text)
        )
        inference_time_seconds += inf_time
        prompt_tokens += pt
        completion_tokens += ct
        code_text, implemented_interface = _extract_code_and_interface(raw_output)

    is_valid_interface, validation_message = _validate_implemented_interface(
        request.language,
        code_text,
        implemented_interface,
    )
    if not is_valid_interface:
        raise ValueError(f"implemented_interface validation failed: {validation_message}")

    code_filename = build_code_filename(request.task_id, request.language)
    code_path = Path(code_output_dir) / request.task_id / code_filename
    raw_output_path = Path(raw_output_dir) / f"{request.task_id}.txt"
    implemented_interface_dir = str(generation_config.get("implemented_interface_dir", ""))
    implemented_interface_path = (
        Path(implemented_interface_dir) / f"{request.task_id}.json"
        if implemented_interface_dir
        else code_path.parent / "implemented_interface.json"
    )
    code_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    implemented_interface_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(code_text, encoding="utf-8")
    raw_output_path.write_text(raw_output, encoding="utf-8")
    implemented_interface_path.write_text(
        json.dumps(implemented_interface, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return CodeGenerationResult(
        task_id=request.task_id,
        case_basename=request.case_basename,
        language=request.language,
        code_file_path=str(code_path),
        raw_output_path=str(raw_output_path),
        implemented_interface_path=str(implemented_interface_path),
        rounds_used=rounds_used,
        inference_time_seconds=inference_time_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        code_text=code_text,
        implemented_interface=implemented_interface,
    )

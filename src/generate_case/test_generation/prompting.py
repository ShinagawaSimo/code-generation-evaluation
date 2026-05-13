import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_MODE_ANALYSIS_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "test_mode_analysis_prompt.txt"
)
DEFAULT_PROGRAM_IO_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "test_generation_program_io_prompt.txt"
)
DEFAULT_FUNCTION_CALL_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "test_generation_function_call_prompt.txt"
)


def load_mode_analysis_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_MODE_ANALYSIS_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def load_test_generation_prompt_for_mode(
    mode: str,
    prompt_path: str | None = None,
) -> str:
    """Load the mode-specific test generation prompt.

    If an explicit prompt_path is provided (e.g. from config), use it directly.
    Otherwise, load the dedicated prompt file for the given test mode.
    """
    if prompt_path:
        return Path(prompt_path).read_text(encoding="utf-8")
    if mode == "function_call":
        return DEFAULT_FUNCTION_CALL_PROMPT_PATH.read_text(encoding="utf-8")
    return DEFAULT_PROGRAM_IO_PROMPT_PATH.read_text(encoding="utf-8")


def build_mode_analysis_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
    relevant_code: str = "",
) -> str:
    payload: Dict[str, Any] = {
        "task_id": task_id,
        "language": language,
        "original_requirement_text": original_requirement_text,
    }
    if relevant_code:
        payload["relevant_code"] = relevant_code
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_test_generation_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
    mode: str,
    mode_reasoning: str,
    relevant_code: str = "",
) -> str:
    payload: Dict[str, Any] = {
        "task_id": task_id,
        "language": language,
        "original_requirement_text": original_requirement_text,
        "test_mode": mode,
        "mode_reasoning": mode_reasoning,
    }
    if relevant_code:
        payload["relevant_code"] = relevant_code
    return json.dumps(payload, ensure_ascii=False, indent=2)

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_MODE_ANALYSIS_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "test_mode_analysis_prompt.txt"
)
DEFAULT_TEST_GENERATION_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "test_generation_prompt.txt"
)


def load_mode_analysis_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_MODE_ANALYSIS_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def load_test_generation_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_TEST_GENERATION_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def build_mode_analysis_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
) -> str:
    return json.dumps(
        {
            "task_id": task_id,
            "language": language,
            "original_requirement_text": original_requirement_text,
        },
        ensure_ascii=False,
        indent=2,
    )


def build_test_generation_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
    mode: str,
    mode_reasoning: str,
) -> str:
    return json.dumps(
        {
            "task_id": task_id,
            "language": language,
            "original_requirement_text": original_requirement_text,
            "test_mode": mode,
            "mode_reasoning": mode_reasoning,
        },
        ensure_ascii=False,
        indent=2,
    )

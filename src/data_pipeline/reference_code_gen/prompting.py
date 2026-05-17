from pathlib import Path
from typing import Dict


def load_reference_code_prompt(prompt_path: str = "") -> str:
    if not prompt_path:
        prompt_path = str(
            Path(__file__).resolve().parents[3] / "src" / "prompts" / "reference_code_generation_prompt.txt"
        )
    return Path(prompt_path).read_text(encoding="utf-8")


def build_reference_code_input(language: str, original_requirement_text: str, relevant_code: str = "") -> str:
    base = (
        f"=== Language ===\n{language}\n\n"
        f"=== Original Requirement ===\n{original_requirement_text}"
    )
    if relevant_code:
        base += f"\n\n=== Relevant Code (provided by test environment — do NOT include in output) ===\n{relevant_code}"
    return base

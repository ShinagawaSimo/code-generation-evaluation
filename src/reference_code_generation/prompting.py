import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "reference_code_generation_prompt.txt"


def load_reference_code_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def build_reference_code_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
) -> str:
    return json.dumps(
        {
            "task_id": task_id,
            "language": language,
            "original_requirement_text": original_requirement_text,
            "output_contract": {
                "approach_enumeration": [
                    {
                        "approach_id": "string",
                        "approach_name": "string",
                        "description": "string",
                    }
                ],
                "implementations": [
                    {
                        "approach_id": "string",
                        "code_text": "string",
                        "implemented_interface": {
                            "interface_type": "function_call | program_io | gui_or_server",
                            "entry_name": "string",
                            "parameters": [
                                {
                                    "name": "string",
                                    "type": "string",
                                    "required": "boolean",
                                }
                            ],
                            "return_type": "string",
                            "notes": ["string"],
                        },
                        "approach_metadata": {
                            "algorithm_type": "string",
                            "complexity": {"time": "string", "space": "string"},
                            "key_characteristics": ["string"],
                        },
                    }
                ],
            },
            "rule_reference": "See prompt for full rule set",
        },
        ensure_ascii=False,
        indent=2,
    )

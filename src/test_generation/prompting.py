import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "test_generation_prompt.txt"


def load_test_generation_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def build_test_generation_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
    requirement_point: Dict[str, Any],
) -> str:
    return json.dumps(
        {
            "task_id": task_id,
            "language": language,
            "original_requirement_text": original_requirement_text,
            "requirement_point": requirement_point,
            "output_contract": {
                "point_id": "string",
                "test_kind": "functional | non_functional",
                "execution_mode": "program_io | function_call | gui_or_server",
                "language": "string",
                "suggested_entry_name": "string",
                "target_signature": {
                    "entry_name": "sort",
                    "parameters": [
                        {
                            "name": "numbers",
                            "type": "string",
                            "required": "boolean"
                        }
                    ],
                    "return_type": "string"
                },
                "function_contract": {
                    "call_style": "positional_only",
                    "parameter_order": ["string"],
                    "notes": ["string"]
                },
                "io_cases": [
                    {
                        "case_id": "string",
                        "description": "string",
                        "input_text": "string",
                        "expected_output_text": "string"
                    }
                ],
                "assertions": [
                    {
                        "assertion_id": "string",
                        "description": "string",
                        "kind": "behavior | performance | type_hint",
                        "call": {
                            "args": [3, 5],
                            "kwargs": {}
                        },
                        "expectation": {
                            "kind": "equals | input_unchanged | new_object | type_hints | max_runtime_seconds | multiset_equals | raises",
                            "expected": {},
                            "metadata": {}
                        }
                    }
                ],
                "environment": {
                    "runtime": "string",
                    "limits": {},
                    "setup_steps": ["string"]
                },
                "artifact_hints": {
                    "suggested_files": ["string"]
                },
                "test_skeleton": {
                    "import_placeholder": "string",
                    "runner_pseudocode": "string"
                }
            },
            "rule_reference": "See prompt for full rule set",
        },
        ensure_ascii=False,
        indent=2,
    )

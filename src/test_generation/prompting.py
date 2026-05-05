import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "test_generation_prompt.txt"


def load_test_generation_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def _build_focus_guidance(requirement_point: Dict[str, Any]) -> Dict[str, Any]:
    point_text = str(requirement_point.get("point_text", ""))
    focus_tags = []
    forbidden_topics = []
    if "命名" in point_text:
        focus_tags.append("function_naming")
        forbidden_topics.extend(["sorting_behavior", "mutation", "duplicates", "empty_input", "reverse", "error_handling"])
    if any(token in point_text for token in ["不得修改", "不修改", "原始输入列表", "原始列表"]):
        focus_tags.append("input_immutability")
        forbidden_topics.extend(["duplicates", "empty_input", "reverse", "error_handling", "new_object"])
    if "重复" in point_text:
        focus_tags.append("duplicate_retention")
        forbidden_topics.extend(["mutation", "empty_input", "reverse", "error_handling"])
    if "空列表" in point_text or ("为空" in point_text and "列表" in point_text):
        focus_tags.append("empty_input")
        forbidden_topics.extend(["duplicates", "mutation", "reverse", "error_handling"])
    if "reverse" in point_text.lower() or "降序" in point_text:
        focus_tags.append("reverse_order")
        forbidden_topics.extend(["default_ascending", "mutation", "duplicates", "error_handling"])
    if "TypeError" in point_text or "ValueError" in point_text or "抛出" in point_text or "异常" in point_text:
        focus_tags.append("exception_behavior")
        forbidden_topics.extend(["normal_sorting", "mutation", "duplicates", "empty_input", "reverse"])
    if "升序" in point_text or "排序" in point_text:
        focus_tags.append("sorting_behavior")
    if "新的列表" in point_text or "新列表" in point_text:
        focus_tags.append("new_object_return")
    return {
        "focus_tags": list(dict.fromkeys(focus_tags)),
        "forbidden_topics": list(dict.fromkeys(forbidden_topics)),
    }


def build_test_generation_input(
    task_id: str,
    language: str,
    original_requirement_text: str,
    expanded_requirement_text: str,
    requirement_point: Dict[str, Any],
) -> str:
    return json.dumps(
        {
            "task_id": task_id,
            "language": language,
            "original_requirement_text": original_requirement_text,
            "expanded_requirement_text": expanded_requirement_text,
            "requirement_point": requirement_point,
            "focus_guidance": _build_focus_guidance(requirement_point),
            "output_contract": {
                "point_id": "string",
                "test_kind": "functional | non_functional",
                "execution_mode": "program_io | function_call | gui_or_server",
                "language": "string",
                "suggested_entry_name": "string",
                "target_signature": {
                    "entry_name": "@@ENTRY_NAME@@ or string",
                    "parameters": [
                        {
                            "name": "@@PARAM_NAME@@ or string",
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
                            "args": [],
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
            "rules": [
                "Return JSON only.",
                "Use strict JSON literals only: strings in double quotes, booleans as true/false, null as null. Never output Python literals like None, True, or False.",
                "Do not use null for object or array fields. Use {} or [] only when schema permits empty value.",
                "If a test input needs Python None semantics, encode it as JSON null.",
                "For program_io, io_cases must use plain text input and plain text expected output.",
                "Generate tests for the current requirement point only. Do not verify other requirement points in the same spec.",
                "If the current point does not mention duplicates, empty input, reverse ordering, mutation, naming, or error handling, do not add assertions for them.",
                "Use at least 3 executable cases for each functional point whenever logically possible. Use at least 4 cases for exception/error-handling points when possible.",
                "For function_call, target_signature must describe one callable entry and assertions must be directly executable without free-form code snippets.",
                "When exact callable name or parameter names are unknown, use placeholders like @@ENTRY_NAME@@ and @@PARAM_NAME@@ instead of leaving fields empty.",
                "For function_call, use positional arguments in call.args whenever possible. Avoid parameter-name-dependent assertions.",
                "For function_call, do not output test_code, pre_call, post_call_check, setup, call_args, input, params, checks, or other custom assertion schemas.",
                "For function_call, every assertion must use only the fixed keys: assertion_id, description, kind, call, expectation.",
                "For function_call, use expectation.kind=raises for exception requirements and put the expected exception type in expectation.expected.",
                "If current point only constrains function naming, execution_mode must be function_call, target_signature.entry_name must equal required name, and assertions should be an empty array.",
                "Add discovery_hint text inside function_contract.notes when callable name is unknown.",
                "Add test_skeleton.import_placeholder and test_skeleton.runner_pseudocode for function_call specs.",
                "For non_functional points, provide environment and assertions even if io_cases is empty.",
                "Do not generate markdown fences.",
                "For function_call, if requirement text names callable entry then use it; otherwise generate suggested_entry_name and also put same name into target_signature.entry_name.",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )

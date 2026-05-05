import json
from pathlib import Path
from typing import Any, Dict

from .models import CodeGenerationRequest


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "code_generation_prompt.txt"


def load_code_generation_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def build_code_generation_input(request: CodeGenerationRequest) -> str:
    payload = request.to_prompt_payload()
    target_filename = build_code_filename(request.task_id, request.language)
    payload["target_filename"] = target_filename
    if request.language == "java":
        payload["java_public_class_name"] = Path(target_filename).stem
    payload["output_contract"] = {
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
    }
    payload["rules"] = [
        "Use only input content provided here.",
        "Do not assume access to local files, tests, tools, or previous stage outputs.",
        "Return JSON only.",
        "Do not use markdown fences.",
        "Try to solve correctly in one round.",
        "implemented_interface must describe actual code you output, not an idealized interface.",
        "If task is function-style, code_text must implement implemented_interface.entry_name exactly.",
        "If task is stdin/stdout style, set interface_type to program_io and entry_name to empty string.",
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_self_review_input(request: CodeGenerationRequest, previous_code: str) -> str:
    payload = request.to_prompt_payload()
    target_filename = build_code_filename(request.task_id, request.language)
    payload["target_filename"] = target_filename
    if request.language == "java":
        payload["java_public_class_name"] = Path(target_filename).stem
    payload["previous_code"] = previous_code
    payload["output_contract"] = {
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
    }
    payload["rules"] = [
        "Revise previous code.",
        "Keep same language.",
        "Return improved JSON only.",
        "Do not use markdown fences.",
        "Do not assume any external files or tests.",
        "implemented_interface must match revised code_text exactly.",
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_code_filename(task_id: str, language: str) -> str:
    mapping = {
        "c": ".c",
        "cpp": ".cpp",
        "python": ".py",
        "java": ".java",
        "rust": ".rs",
        "go": ".go",
        "typescript": ".ts",
        "javascript": ".js",
    }
    return f"main_{task_id}{mapping[language]}"

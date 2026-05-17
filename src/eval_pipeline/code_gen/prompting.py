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
    payload["rule_reference"] = "See prompt for full rule set"
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
    payload["rule_reference"] = "See prompt for full rule set"
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

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CodeGenerationRequest:
    task_id: str
    case_basename: str
    language: str
    original_requirement_text: str
    acceptance_standard: Dict[str, Any] = field(default_factory=dict)
    relevant_code: str = ""

    def to_prompt_payload(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "case_basename": self.case_basename,
            "language": self.language,
            "original_requirement_text": self.original_requirement_text,
            "acceptance_standard": self.acceptance_standard,
            "relevant_code": self.relevant_code,
        }


@dataclass
class CodeGenerationResult:
    task_id: str
    case_basename: str
    language: str
    code_file_path: str
    raw_output_path: str
    implemented_interface_path: str
    rounds_used: int
    inference_time_seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    code_text: str = ""
    implemented_interface: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "case_basename": self.case_basename,
            "language": self.language,
            "code_file_path": self.code_file_path,
            "implemented_interface_path": self.implemented_interface_path,
            "rounds_used": self.rounds_used,
            "inference_time_seconds": self.inference_time_seconds,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "implemented_interface": dict(self.implemented_interface),
        }

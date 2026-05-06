from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal


ExecutionMode = Literal["program_io", "function_call", "gui_or_server"]
TestKind = Literal["functional", "non_functional"]


@dataclass
class GeneratedTestArtifact:
    relative_path: str
    content: str


@dataclass
class RequirementPointTestSpec:
    point_id: str
    point_text: str
    category: str
    test_kind: TestKind
    execution_mode: ExecutionMode
    language: str
    suggested_entry_name: str = ""
    target_signature: Dict[str, Any] = field(default_factory=dict)
    function_contract: Dict[str, Any] = field(default_factory=dict)
    io_cases: List[Dict[str, Any]] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    artifact_hints: Dict[str, Any] = field(default_factory=dict)
    test_skeleton: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "point_text": self.point_text,
            "category": self.category,
            "test_kind": self.test_kind,
            "execution_mode": self.execution_mode,
            "language": self.language,
            "suggested_entry_name": self.suggested_entry_name,
            "target_signature": self.target_signature,
            "function_contract": self.function_contract,
            "io_cases": self.io_cases,
            "assertions": self.assertions,
            "environment": self.environment,
            "artifact_hints": self.artifact_hints,
            "test_skeleton": self.test_skeleton,
        }


@dataclass
class TestGenerationResult:
    task_id: str
    language: str
    point_specs: List[RequirementPointTestSpec] = field(default_factory=list)
    generated_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "point_specs": [point_spec.to_dict() for point_spec in self.point_specs],
            "generated_files": list(self.generated_files),
        }

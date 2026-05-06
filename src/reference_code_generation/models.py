from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ReferenceImplementation:
    code_text: str
    implemented_interface: Dict[str, Any] = field(default_factory=dict)
    approach_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code_text": self.code_text,
            "implemented_interface": dict(self.implemented_interface),
            "approach_metadata": dict(self.approach_metadata),
        }


@dataclass
class ReferenceCodeResult:
    task_id: str
    language: str
    reference_implementations: List[ReferenceImplementation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "reference_implementations": [impl.to_dict() for impl in self.reference_implementations],
        }

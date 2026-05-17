from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ReferenceImplementation:
    approach_id: str
    approach_name: str
    description: str
    code_file_path: str
    interface_type: str
    entry_name: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: str = ""
    approach_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceCodeResult:
    task_id: str
    language: str
    code_output_dir: str
    implementations: List[ReferenceImplementation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "code_output_dir": self.code_output_dir,
            "reference_implementations": [
                {
                    "approach_id": impl.approach_id,
                    "approach_name": impl.approach_name,
                    "description": impl.description,
                    "code_file_path": impl.code_file_path,
                    "interface_type": impl.interface_type,
                    "entry_name": impl.entry_name,
                    "parameters": impl.parameters,
                    "return_type": impl.return_type,
                    "approach_metadata": impl.approach_metadata,
                }
                for impl in self.implementations
            ],
        }

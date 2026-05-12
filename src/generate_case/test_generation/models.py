from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GeneratedTestArtifact:
    relative_path: str
    content: str


@dataclass
class TestGenerationResult:
    task_id: str
    language: str
    generated_files: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "generated_files": self.generated_files,
        }

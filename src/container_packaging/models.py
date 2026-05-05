from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ContainerPackagingResult:
    task_id: str
    language: str
    container_dir: str
    generated_files: List[str] = field(default_factory=list)
    summary: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "container_dir": self.container_dir,
            "generated_files": list(self.generated_files),
            "summary": dict(self.summary),
        }

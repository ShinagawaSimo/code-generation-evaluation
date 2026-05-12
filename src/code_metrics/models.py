from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ApproachCodeBLEU:
    approach_id: str
    approach_name: str
    codebleu_score: float


@dataclass
class CodeMetricsResult:
    task_id: str
    compile_success: bool
    run_success: bool
    compile_runtime_success: bool
    test_results: Dict[str, Any] = field(default_factory=dict)
    codebleu: Dict[str, Any] = field(default_factory=dict)
    inference_time_seconds: float = 0.0
    total_tokens: int = 0
    comment_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "compile_success": self.compile_success,
            "run_success": self.run_success,
            "compile_runtime_success": self.compile_runtime_success,
            "test_results": dict(self.test_results),
            "codebleu": dict(self.codebleu),
            "inference_time_seconds": self.inference_time_seconds,
            "total_tokens": self.total_tokens,
            "comment_ratio": self.comment_ratio,
        }

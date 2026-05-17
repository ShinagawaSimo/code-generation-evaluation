from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CodeExecutionResult:
    task_id: str
    language: str
    container_dir: str
    compile_success: bool
    tests_success: bool
    passed_test_count: int = 0
    failed_test_count: int = 0
    skipped_count: int = 0
    has_skipped_tests: bool = False
    failure_message: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "container_dir": self.container_dir,
            "compile_success": self.compile_success,
            "tests_success": self.tests_success,
            "passed_test_count": self.passed_test_count,
            "failed_test_count": self.failed_test_count,
            "skipped_count": self.skipped_count,
            "has_skipped_tests": self.has_skipped_tests,
            "failure_message": self.failure_message,
            "summary": dict(self.summary),
        }

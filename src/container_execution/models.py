from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ContainerExecutionResult:
    task_id: str
    language: str
    image_tag: str
    container_dir: str
    environment_ready: bool
    image_build_success: bool
    compile_success: bool
    run_success: bool
    tests_success: bool
    has_skipped_tests: bool = False
    skipped_count: int = 0
    passed_test_count: int = 0
    failed_test_count: int = 0
    build_log_path: str = ""
    run_log_path: str = ""
    execution_summary_path: str = ""
    failure_message: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "image_tag": self.image_tag,
            "container_dir": self.container_dir,
            "environment_ready": self.environment_ready,
            "image_build_success": self.image_build_success,
            "compile_success": self.compile_success,
            "run_success": self.run_success,
            "tests_success": self.tests_success,
            "has_skipped_tests": self.has_skipped_tests,
            "skipped_count": self.skipped_count,
            "passed_test_count": self.passed_test_count,
            "failed_test_count": self.failed_test_count,
            "build_log_path": self.build_log_path,
            "run_log_path": self.run_log_path,
            "execution_summary_path": self.execution_summary_path,
            "failure_message": self.failure_message,
            "summary": dict(self.summary),
        }

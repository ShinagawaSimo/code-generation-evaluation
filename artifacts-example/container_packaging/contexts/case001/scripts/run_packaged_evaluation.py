import json
import subprocess
from pathlib import Path

WORKSPACE = Path("/workspace")
SUMMARY_PATH = WORKSPACE / "execution_summary.json"
COMPILE_COMMAND = "python3 -m py_compile code/main_case001.py"
TEST_COMMAND = "python3 /workspace/scripts/run_packaged_tests.py"


def _run_shell(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", "-lc", command],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
    )


def _write_summary(summary: dict) -> None:
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    summary = {
        "compile_success": False,
        "tests_success": False,
        "has_skipped_tests": False,
        "skipped_count": 0,
        "failed_test_count": 0,
        "passed_test_count": 0,
        "compile_returncode": None,
        "tests_returncode": None,
        "failure_stage": "",
        "failure_message": "",
    }
    print("[container] compile/setup")
    compile_result = _run_shell(COMPILE_COMMAND)
    summary["compile_returncode"] = compile_result.returncode
    summary["compile_stdout"] = compile_result.stdout
    summary["compile_stderr"] = compile_result.stderr
    summary["compile_success"] = compile_result.returncode == 0
    if not summary["compile_success"]:
        summary["failure_stage"] = "compile"
        summary["failure_message"] = "compile/setup failed"
        _write_summary(summary)
        return 1
    print("[container] run packaged tests")
    tests_result = _run_shell(TEST_COMMAND)
    summary["tests_returncode"] = tests_result.returncode
    summary["tests_stdout"] = tests_result.stdout
    summary["tests_stderr"] = tests_result.stderr
    report_path = WORKSPACE / "test_report.json"
    report = []
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    summary["passed_test_count"] = sum(1 for item in report if item.get("status") == "passed")
    summary["failed_test_count"] = sum(1 for item in report if item.get("status") == "failed")
    summary["skipped_count"] = sum(1 for item in report if item.get("status") == "skipped")
    summary["has_skipped_tests"] = summary["skipped_count"] > 0
    summary["tests_success"] = summary["failed_test_count"] == 0 and tests_result.returncode == 0
    if not summary["tests_success"]:
        summary["failure_stage"] = "tests"
        summary["failure_message"] = "packaged tests failed"
    _write_summary(summary)
    return 0 if summary["tests_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

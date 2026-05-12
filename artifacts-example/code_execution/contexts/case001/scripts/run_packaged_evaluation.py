import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/workspace")
SUMMARY_PATH = WORKSPACE / "execution_summary.json"
RESULTS_DIR = WORKSPACE / "results"

COMPILE_COMMAND = "python3 -m py_compile code/main_case001.py"


def _write_summary(summary: dict) -> None:
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def main() -> int:
    summary = {
        "compile_success": False,
        "tests_success": False,
        "passed_test_count": 0,
        "failed_test_count": 0,
        "skipped_count": 0,
        "has_skipped_tests": False,
        "failure_message": "",
    }

    print("[evaluation] compile phase", flush=True)
    compile_result = subprocess.run(
        ["sh", "-lc", COMPILE_COMMAND],
        cwd=str(WORKSPACE), text=True, capture_output=True, timeout=120,
    )
    summary["compile_success"] = compile_result.returncode == 0
    if not summary["compile_success"]:
        summary["failure_message"] = (
            f"Compile error (exit={compile_result.returncode}):\n{compile_result.stderr[:500]}"
        )
        _write_summary(summary)
        return 1

    print("[evaluation] test phase", flush=True)
    test_runner = WORKSPACE / "scripts" / "run_tests.py"
    test_result = subprocess.run(
        [sys.executable, str(test_runner)],
        cwd=str(WORKSPACE), text=True, capture_output=True, timeout=120,
    )

    if test_result.stdout:
        print("[test_runner stdout]", flush=True)
        for line in test_result.stdout.splitlines():
            print(f"  {line}", flush=True)
    if test_result.stderr:
        print("[test_runner stderr]", flush=True)
        for line in test_result.stderr.splitlines():
            print(f"  {line}", flush=True)

    all_results: list[dict] = []
    if RESULTS_DIR.exists():
        for rf in sorted(RESULTS_DIR.glob("*.json")):
            try:
                all_results.append(json.loads(rf.read_text(encoding="utf-8")))
            except Exception:
                pass

    if test_result.returncode != 0 and not all_results:
        summary["failure_message"] = (
            f"Test runner failed (exit={test_result.returncode}):\n"
            f"stdout: {test_result.stdout[:300]}\n"
            f"stderr: {test_result.stderr[:300]}"
        )
        _write_summary(summary)
        print(f"[evaluation] FAILED — {summary['failure_message']}", flush=True)
        return 1

    if not all_results:
        summary["failure_message"] = "No test results found — test runner produced zero result files"
        _write_summary(summary)
        print(f"[evaluation] FAILED — {summary['failure_message']}", flush=True)
        return 1

    summary["passed_test_count"] = sum(1 for r in all_results if r.get("passed"))
    summary["failed_test_count"] = sum(1 for r in all_results if not r.get("passed"))
    summary["tests_success"] = summary["failed_test_count"] == 0

    print(f"[evaluation] results: {summary['passed_test_count']} passed, {summary['failed_test_count']} failed, {len(all_results)} total", flush=True)
    for r in all_results:
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"  [{status}] {r.get('test_id')}", flush=True)

    if not summary["tests_success"]:
        summary["failure_message"] = f"{summary['failed_test_count']} test(s) failed"

    _write_summary(summary)
    return 0 if summary["tests_success"] else 1


if __name__ == "__main__":
    sys.exit(main())

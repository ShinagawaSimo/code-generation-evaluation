from __future__ import annotations

import subprocess
from typing import Any, Dict, List


def _normalize_text(value: Any) -> str:
    """
    Normalize input values into a trimmed string.
    value: raw input (None, list, or scalar) to be normalized.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value).strip()
    return str(value).strip()


def run_sample_tests(
    run_command: List[str],
    samples: List[Dict[str, Any]],
    workspace: str,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    """
    Run sample test cases and compare stdout with expected outputs.
    run_command: executable command list used to run the program.
    samples: list of sample cases with input and expected output fields.
    workspace: working directory for process execution.
    timeout_seconds: per-case timeout to avoid hanging runs.
    """
    results = []
    all_passed = True
    for sample in samples:
        input_data = _normalize_text(sample.get("input") or sample.get("stdin"))
        expected = _normalize_text(sample.get("expected_output") or sample.get("output"))
        completed = subprocess.run(
            run_command,
            input=input_data,
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=timeout_seconds,
        )
        actual = _normalize_text(completed.stdout)
        passed = completed.returncode == 0 and actual == expected
        all_passed = all_passed and passed
        results.append(
            {
                "input": input_data,
                "expected_output": expected,
                "actual_output": actual,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "passed": passed,
            }
        )
    return {"passed": all_passed, "cases": results}

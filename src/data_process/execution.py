from __future__ import annotations

import os
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


def _safe_env() -> Dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
    }


def _truncate_text(value: str, limit: int = 10000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit]

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
        try:
            completed = subprocess.run(
                run_command,
                input=input_data,
                capture_output=True,
                text=True,
                cwd=workspace,
                timeout=timeout_seconds,
                env=_safe_env(),
            )
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            returncode = completed.returncode
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or ""
            stderr = error.stderr or "timeout"
            returncode = -1
        actual = _normalize_text(stdout)
        passed = returncode == 0 and actual == expected
        all_passed = all_passed and passed
        results.append(
            {
                "input": input_data,
                "expected_output": expected,
                "actual_output": actual,
                "returncode": returncode,
                "stdout": _truncate_text(stdout),
                "stderr": _truncate_text(stderr),
                "passed": passed,
            }
        )
    return {"passed": all_passed, "cases": results}

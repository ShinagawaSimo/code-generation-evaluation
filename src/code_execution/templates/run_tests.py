import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/workspace")
MANIFEST_PATH = WORKSPACE / "tests" / "manifest.json"
RESULTS_DIR = WORKSPACE / "results"


def _run_single_test(test_path: Path, test_id: str) -> dict:
    result_path = RESULTS_DIR / f"{test_id}.json"
    suffix = test_path.suffix.lower()

    if suffix == ".py":
        runner = [sys.executable, str(test_path)]
    elif suffix == ".js":
        runner = ["node", str(test_path)]
    else:
        return {"test_id": test_id, "passed": False, "actual": None, "expected": None, "stderr": f"unsupported test file: {test_path.name}"}

    try:
        proc = subprocess.run(
            runner, cwd=str(WORKSPACE), text=True, capture_output=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"test_id": test_id, "passed": False, "actual": None, "expected": None, "stderr": "timeout (30s)"}

    if result_path.exists():
        try:
            return json.loads(result_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"test_id": test_id, "passed": proc.returncode == 0, "actual": None, "expected": None, "stderr": proc.stderr[:500]}


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not MANIFEST_PATH.exists():
        result = {"test_id": "unknown", "passed": False, "actual": None, "expected": None, "stderr": "manifest.json not found"}
        (RESULTS_DIR / "manifest_error.json").write_text(json.dumps(result), encoding="utf-8")
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tests = manifest.get("tests", [])

    all_passed = True
    for test in tests:
        test_id = test["test_id"]
        filename = test["filename"]
        test_path = WORKSPACE / "tests" / filename
        if not test_path.exists():
            result = {"test_id": test_id, "passed": False, "actual": None, "expected": None, "stderr": "test file not found"}
            (RESULTS_DIR / f"{test_id}.json").write_text(json.dumps(result), encoding="utf-8")
            all_passed = False
            continue
        result = _run_single_test(test_path, test_id)
        result_path = RESULTS_DIR / f"{test_id}.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        if not result.get("passed"):
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

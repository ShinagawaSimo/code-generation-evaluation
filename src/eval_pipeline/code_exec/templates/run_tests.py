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

    print(f"  [{test_id}] running: {' '.join(runner)}", flush=True)
    try:
        proc = subprocess.run(
            runner, cwd=str(WORKSPACE), text=True, capture_output=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(f"  [{test_id}] TIMEOUT (30s)", flush=True)
        return {"test_id": test_id, "passed": False, "actual": None, "expected": None, "stderr": "timeout (30s)"}

    if result_path.exists():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _print_result(result)
            return result
        except Exception:
            pass
    result = {"test_id": test_id, "passed": proc.returncode == 0, "actual": None, "expected": None, "stderr": proc.stderr[:500]}
    _print_result(result)
    return result


def _print_result(result: dict) -> None:
    test_id = result.get("test_id", "?")
    passed = result.get("passed", False)
    status = "PASS" if passed else "FAIL"
    actual = _truncate(str(result.get("actual")))
    expected = _truncate(str(result.get("expected")))
    stderr = str(result.get("stderr", ""))
    print(f"  [{test_id}] {status}", flush=True)
    if not passed:
        print(f"         actual:   {actual}", flush=True)
        print(f"         expected: {expected}", flush=True)
        if stderr:
            print(f"         stderr:   {_truncate(stderr, 200)}", flush=True)


def _truncate(text: str, limit: int = 150) -> str:
    text = text.replace("\n", "\\n")
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not MANIFEST_PATH.exists():
        result = {"test_id": "unknown", "passed": False, "actual": None, "expected": None, "stderr": "manifest.json not found"}
        (RESULTS_DIR / "manifest_error.json").write_text(json.dumps(result), encoding="utf-8")
        print("[test_runner] ERROR: manifest.json not found", flush=True)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tests = manifest.get("tests", [])
    print(f"[test_runner] running {len(tests)} test(s)...", flush=True)

    all_passed = True
    for test in tests:
        test_id = test["test_id"]
        filename = test["filename"]
        test_path = WORKSPACE / "tests" / filename
        if not test_path.exists():
            result = {"test_id": test_id, "passed": False, "actual": None, "expected": None, "stderr": "test file not found"}
            (RESULTS_DIR / f"{test_id}.json").write_text(json.dumps(result), encoding="utf-8")
            print(f"  [{test_id}] FAIL — file not found: {filename}", flush=True)
            all_passed = False
            continue
        result = _run_single_test(test_path, test_id)
        result_path = RESULTS_DIR / f"{test_id}.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        if not result.get("passed"):
            all_passed = False

    passed = sum(1 for t in tests if (RESULTS_DIR / f"{t['test_id']}.json").exists()
                 and json.loads((RESULTS_DIR / f"{t['test_id']}.json").read_text(encoding="utf-8")).get("passed"))
    print(f"[test_runner] {passed}/{len(tests)} passed", flush=True)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

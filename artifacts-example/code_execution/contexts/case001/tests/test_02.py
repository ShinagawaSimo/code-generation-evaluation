import json, sys, traceback
from pathlib import Path
from typing import Any

_RESULTS_DIR = Path("/workspace/results")
_RESULT_PATH = _RESULTS_DIR / "sort_empty_input.json"

def _safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)

def test():
    import importlib.util, sys
    from pathlib import Path
    _code_files = sorted((Path('/workspace/code')).iterdir())
    _code_file = next(f for f in _code_files if f.is_file())
    _spec = importlib.util.spec_from_file_location("_test_solution", _code_file)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _fn = getattr(_mod, "sort")
    _result = _fn([])
    _expected = []
    _passed = _result == _expected
    return _passed, _result, _expected


if __name__ == "__main__":
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        passed, actual, expected = test()
        err = ""
    except Exception as _exc:
        passed = False
        actual = None
        expected = None
        err = traceback.format_exc()
    _RESULT_PATH.write_text(
        json.dumps({
            "test_id": "sort_empty_input",
            "passed": passed,
            "actual": _safe(actual),
            "expected": _safe(expected),
            "stderr": err,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    sys.exit(0 if passed else 1)

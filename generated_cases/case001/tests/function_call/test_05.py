import json, sys, traceback
from pathlib import Path
from typing import Any

_RESULTS_DIR = Path("/workspace/results")
_RESULT_PATH = _RESULTS_DIR / "sort_type_hints.json"

def _safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)

def test():
    from typing import get_type_hints
    import inspect
    import importlib.util, sys
    from pathlib import Path
    _code_files = sorted((Path('/workspace/code')).iterdir())
    _code_file = next(f for f in _code_files if f.is_file())
    _spec = importlib.util.spec_from_file_location("_test_solution", _code_file)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _fn = getattr(_mod, "sort")
    _hints = get_type_hints(_fn)
    _sig = inspect.signature(_fn)
    _expected = {}
    _passed = True
    for _name, _exp_hint in _expected.items():
        _actual_hint = _hints.get(_name)
        _actual_text = getattr(_actual_hint, '__name__', str(_actual_hint)) if _actual_hint is not None else ''
        if str(_exp_hint) not in _actual_text:
            _passed = False
    _return_hint = _hints.get('return', _sig.return_annotation)
    _return_text = str(_return_hint) if _return_hint is not inspect.Signature.empty else ''
    if 'return' in _expected and str(_expected['return']) not in _return_text:
        _passed = False
    return _passed, {k: str(v) for k, v in _hints.items()}, _expected


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
            "test_id": "sort_type_hints",
            "passed": passed,
            "actual": _safe(actual),
            "expected": _safe(expected),
            "stderr": err,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    sys.exit(0 if passed else 1)

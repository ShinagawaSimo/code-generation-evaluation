import json
from pathlib import Path
from typing import Any, Callable, List, Tuple

from ..models import GeneratedTestArtifact


_PYTHON_HEADER = """\
import json, sys, traceback
from pathlib import Path
from typing import Any

_RESULTS_DIR = Path("/workspace/results")
_RESULT_PATH = _RESULTS_DIR / "{test_id}.json"

def _safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)

def test():
{test_body}

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
        json.dumps({{
            "test_id": "{test_id}",
            "passed": passed,
            "actual": _safe(actual),
            "expected": _safe(expected),
            "stderr": err,
        }}, ensure_ascii=False),
        encoding="utf-8",
    )
    sys.exit(0 if passed else 1)
"""


_JAVASCRIPT_HEADER = """\
const fs = require("fs");
const path = require("path");

const RESULTS_DIR = "/workspace/results";
const RESULT_PATH = path.join(RESULTS_DIR, "{test_id}.json");

function _safe(obj) {{
    try {{ return JSON.stringify(obj); }} catch(e) {{ return String(obj); }}
}}

function test() {{
{test_body}
}}

try {{
    const [passed, actual, expected] = test();
    var stderr = "";
}} catch (exc) {{
    var passed = false;
    var actual = null;
    var expected = null;
    var stderr = exc.stack || String(exc);
}}
fs.mkdirSync(RESULTS_DIR, {{ recursive: true }});
fs.writeFileSync(RESULT_PATH, JSON.stringify({{
    test_id: "{test_id}",
    passed: passed,
    actual: _safe(actual),
    expected: _safe(expected),
    stderr: stderr,
}}), "utf-8");
process.exit(passed ? 0 : 1);
"""


def _format_python_value(value: Any) -> str:
    if isinstance(value, list):
        items = ", ".join(_format_python_value(item) for item in value)
        return f"[{items}]"
    if isinstance(value, dict):
        items = ", ".join(
            f"{_format_python_key(k)}: {_format_python_value(v)}"
            for k, v in value.items()
        )
        return f"{{{items}}}"
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    return repr(value)


def _format_python_key(key: str) -> str:
    return repr(key)


def _format_js_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def make_python_test_file(test_id: str, test_body: str) -> str:
    return _PYTHON_HEADER.format(test_id=test_id, test_body=test_body)


def make_javascript_test_file(test_id: str, test_body: str) -> str:
    return _JAVASCRIPT_HEADER.format(test_id=test_id, test_body=test_body)


def build_python_import_expression(entry_name: str) -> str:
    return (
        "import importlib.util, sys\n"
        "    from pathlib import Path\n"
        "    _code_files = sorted((Path('/workspace/code')).iterdir())\n"
        "    _code_file = next(f for f in _code_files if f.is_file())\n"
        f'    _spec = importlib.util.spec_from_file_location("_test_solution", _code_file)\n'
        "    _mod = importlib.util.module_from_spec(_spec)\n"
        "    _spec.loader.exec_module(_mod)\n"
        f"    _fn = getattr(_mod, \"{entry_name}\")\n"
    )


def build_python_call_expression(args: List[Any], kwargs: dict) -> str:
    args_str = ", ".join(_format_python_value(a) for a in args)
    kwargs_str = ", ".join(f"{k}={_format_python_value(v)}" for k, v in kwargs.items())
    parts = [p for p in [args_str, kwargs_str] if p]
    return ", ".join(parts)


def build_manifest(tests: List[dict], execution_mode: str, language: str) -> dict:
    return {
        "execution_mode": execution_mode,
        "language": language,
        "tests": [
            {"test_id": t["test_id"], "filename": t["filename"]}
            for t in tests
        ],
    }

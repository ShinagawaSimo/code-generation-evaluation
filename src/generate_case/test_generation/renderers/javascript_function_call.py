import json
from typing import Any, Dict, List

from ..models import GeneratedTestArtifact
from .base import make_javascript_test_file


def render(test: Dict[str, Any], entry_name: str, index: int = 1, relevant_code: str = "", class_defs: Dict[str, List[str]] | None = None) -> GeneratedTestArtifact:
    test_id = str(test["test_id"])
    call = test.get("call", {})
    args: list = list(call.get("args", []))
    kwargs: dict = dict(call.get("kwargs", {}))
    expectation = test.get("expectation", {})
    kind = str(expectation.get("kind", "equals"))
    expected = expectation.get("expected")

    test_body = _build_js_test_body(kind, entry_name, args, kwargs, expected)
    full_source = make_javascript_test_file(test_id, test_body)
    filename = f"test_{index:02d}.js"
    return GeneratedTestArtifact(filename, full_source)


def _build_js_test_body(kind: str, entry_name: str, args: list, kwargs: dict, expected: Any) -> str:
    args_str = ", ".join(json.dumps(a, ensure_ascii=False) for a in args)
    expected_str = json.dumps(expected, ensure_ascii=False) if expected is not None else "null"

    import_code = (
        f'    const _mod = require("/workspace/code");\n'
        f'    const _fn = _mod["{entry_name}"] || (_mod.default && _mod.default["{entry_name}"]) || _mod.default;\n'
    )

    if kind == "raises":
        return (
            f"{import_code}"
            f"    try {{\n"
            f"        _fn({args_str});\n"
            f"        return [false, null, null];\n"
            f"    }} catch (exc) {{\n"
            f"        return [true, exc.name, exc.message];\n"
            f"    }}\n"
        )

    return (
        f"{import_code}"
        f"    const _result = _fn({args_str});\n"
        f"    const _expected = {expected_str};\n"
        f"    const _passed = JSON.stringify(_result) === JSON.stringify(_expected);\n"
        f"    return [_passed, _result, _expected];\n"
    )

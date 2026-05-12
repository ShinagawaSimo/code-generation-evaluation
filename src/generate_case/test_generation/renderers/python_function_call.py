from typing import Any, Dict, List

from ..models import GeneratedTestArtifact
from .base import (
    build_python_call_expression,
    build_python_import_expression,
    make_python_test_file,
)


def render(test: Dict[str, Any], entry_name: str, index: int = 1) -> GeneratedTestArtifact:
    test_id = str(test["test_id"])
    call = test.get("call", {})
    args: List[Any] = list(call.get("args", []))
    kwargs: dict = dict(call.get("kwargs", {}))
    expectation = test.get("expectation", {})
    kind = str(expectation.get("kind", "equals"))
    expected = expectation.get("expected")

    test_body = _build_test_body(kind, entry_name, args, kwargs, expected)
    full_source = make_python_test_file(test_id, test_body)
    filename = f"test_{index:02d}.py"
    return GeneratedTestArtifact(filename, full_source)


def _build_test_body(kind: str, entry_name: str, args: List[Any], kwargs: dict, expected: Any) -> str:
    import_expr = build_python_import_expression(entry_name)
    call_expr = build_python_call_expression(args, kwargs)

    if kind == "raises":
        return (
            f"    {import_expr}"
            f"    import traceback\n"
            f"    try:\n"
            f"        _fn({call_expr})\n"
            f"        return False, None, None\n"
            f"    except Exception as _e:\n"
            f"        return True, type(_e).__name__, traceback.format_exc()\n"
        )

    if kind == "input_unchanged":
        return (
            f"    import copy\n"
            f"    {import_expr}"
            f"    _input = {_format_call_args(args, kwargs)}\n"
            f"    _snapshot = copy.deepcopy(_input)\n"
            f"    _result = _fn({call_expr})\n"
            f"    _passed = _input == _snapshot\n"
            f"    return _passed, _input, _snapshot\n"
        )

    if kind == "new_object":
        return (
            f"    {import_expr}"
            f"    _input = {_format_call_args(args, kwargs)}\n"
            f"    _result = _fn({call_expr})\n"
            f"    _passed = _result is not _input\n"
            f"    return _passed, id(_result), id(_input)\n"
        )

    if kind == "type_hints":
        return (
            f"    from typing import get_type_hints\n"
            f"    import inspect\n"
            f"    {import_expr}"
            f"    _hints = get_type_hints(_fn)\n"
            f"    _sig = inspect.signature(_fn)\n"
            f'    _expected = {repr(expected) if expected is not None else "{}"}\n'
            f"    _passed = True\n"
            f"    for _name, _exp_hint in _expected.items():\n"
            f"        _actual_hint = _hints.get(_name)\n"
            f"        _actual_text = getattr(_actual_hint, '__name__', str(_actual_hint)) if _actual_hint is not None else ''\n"
            f"        if str(_exp_hint) not in _actual_text:\n"
            f"            _passed = False\n"
            f"    _return_hint = _hints.get('return', _sig.return_annotation)\n"
            f"    _return_text = str(_return_hint) if _return_hint is not inspect.Signature.empty else ''\n"
            f"    if 'return' in _expected and str(_expected['return']) not in _return_text:\n"
            f"        _passed = False\n"
            f"    return _passed, {{k: str(v) for k, v in _hints.items()}}, _expected\n"
        )

    if kind == "max_runtime_seconds":
        max_sec = float(expected) if expected is not None else 1.0
        return (
            f"    import time\n"
            f"    {import_expr}"
            f"    _start = time.perf_counter()\n"
            f"    _fn({call_expr})\n"
            f"    _elapsed = time.perf_counter() - _start\n"
            f"    _passed = _elapsed <= {max_sec}\n"
            f"    return _passed, _elapsed, {max_sec}\n"
        )

    if kind == "multiset_equals":
        return (
            f"    from collections import Counter\n"
            f"    {import_expr}"
            f"    _result = _fn({call_expr})\n"
            f"    _expected = {_format_value(expected)}\n"
            f"    _passed = Counter(_result) == Counter(_expected)\n"
            f"    return _passed, list(_result) if hasattr(_result, '__iter__') else _result, _expected\n"
        )

    return (
        f"    {import_expr}"
        f"    _result = _fn({call_expr})\n"
        f"    _expected = {_format_value(expected)}\n"
        f"    _passed = _result == _expected\n"
        f"    return _passed, _result, _expected\n"
    )


def _format_call_args(args: list, kwargs: dict) -> str:
    from .base import _format_python_value
    if args:
        return _format_python_value(args[0])
    if kwargs:
        first_key = next(iter(kwargs))
        return _format_python_value(kwargs[first_key])
    return "None"


def _format_value(value) -> str:
    from .base import _format_python_value
    if value is None:
        return "None"
    return _format_python_value(value)

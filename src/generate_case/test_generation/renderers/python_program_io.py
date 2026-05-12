from typing import Any, Dict, List

from ..models import GeneratedTestArtifact
from .base import make_python_test_file


def _param_type_parse_expr(param_type: str) -> str:
    t = param_type.strip().lower()
    if t in ("list", "list[int]", "list[float]", "list[str]", "array"):
        return "[int(x) if x.lstrip('-').isdigit() else x for x in _line.split()]"
    if t in ("int", "integer"):
        return "int(_line.strip())"
    if t == "float":
        return "float(_line.strip())"
    return "_line"


def _return_type_format_expr(return_type: str) -> str:
    t = return_type.strip().lower()
    if t in ("list", "list[int]", "list[float]", "list[str]", "array"):
        return "' '.join(str(x) for x in _result)"
    return "str(_result)"


def _build_import_block(entry_name: str) -> str:
    return (
        '    import importlib.util, sys\n'
        '    from pathlib import Path\n'
        '    _code_files = sorted((Path(\"/workspace/code\")).iterdir())\n'
        '    _code_file = next(f for f in _code_files if f.is_file())\n'
        f'    _spec = importlib.util.spec_from_file_location("_solution", _code_file)\n'
        '    _mod = importlib.util.module_from_spec(_spec)\n'
        '    _spec.loader.exec_module(_mod)\n'
        f'    _fn = getattr(_mod, "{entry_name}")\n'
    )


def render(test: Dict[str, Any], entry_name: str, index: int = 1) -> GeneratedTestArtifact:
    test_id = str(test["test_id"])
    io_case = test.get("io_case", {})
    input_text = str(io_case.get("input_text", ""))
    expected_output = str(io_case.get("expected_output_text", ""))

    parameters: List[dict] = list(test.get("parameters", []))
    param_type = str(parameters[0].get("type", "string")) if parameters else "string"
    return_type = str(test.get("return_type", "string"))

    parse_expr = _param_type_parse_expr(param_type)
    format_expr = _return_type_format_expr(return_type)
    import_repr = repr(input_text)
    expected_repr = repr(expected_output)

    test_body = (
        f'{_build_import_block(entry_name)}'
        f'    _input_text = {import_repr}\n'
        f'    _output_lines = []\n'
        f'    for _line in _input_text.split("\\n"):\n'
        f'        _parsed = {parse_expr}\n'
        f'        _result = _fn(_parsed)\n'
        f'        _output_lines.append({format_expr})\n'
        f'    _actual = "\\n".join(_output_lines)\n'
        f'    _expected = {expected_repr}\n'
        f'    _passed = _actual == _expected\n'
        f'    return _passed, _actual, _expected\n'
    )

    full_source = make_python_test_file(test_id, test_body)
    filename = f"test_{index:02d}.py"
    return GeneratedTestArtifact(filename, full_source)

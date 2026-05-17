import json
from typing import Any, Dict, List

from ..models import GeneratedTestArtifact
from .base import make_javascript_test_file


def _param_type_parse_expr(param_type: str) -> str:
    t = param_type.strip().lower()
    if t in ("list", "list[int]", "list[float]", "list[str]", "array"):
        return "_line.trim().split(/\\s+/).map(x => isNaN(Number(x)) ? x : Number(x))"
    if t in ("int", "integer"):
        return "parseInt(_line.trim(), 10)"
    if t == "float":
        return "parseFloat(_line.trim())"
    return "_line"


def _return_type_format_expr(return_type: str) -> str:
    t = return_type.strip().lower()
    if t in ("list", "list[int]", "list[float]", "list[str]", "array"):
        return "_result.join(' ')"
    return "String(_result)"


def _build_import_block(entry_name: str) -> str:
    return (
        '    const path = require("path");\n'
        '    const fs = require("fs");\n'
        '    const codeDir = "/workspace/code";\n'
        '    const codeFile = fs.readdirSync(codeDir).find(f => fs.statSync(path.join(codeDir, f)).isFile());\n'
        '    const _mod = require(path.join(codeDir, codeFile));\n'
        f'    const _fn = _mod["{entry_name}"] || (_mod.default && _mod.default["{entry_name}"]) || _mod.default;\n'
    )


def render(test: Dict[str, Any], entry_name: str, index: int = 1, relevant_code: str = "", class_defs: Dict[str, List[str]] | None = None) -> GeneratedTestArtifact:
    test_id = str(test["test_id"])
    io_case = test.get("io_case", {})
    input_text = str(io_case.get("input_text", ""))
    expected_output = str(io_case.get("expected_output_text", ""))

    parameters: List[dict] = list(test.get("parameters", []))
    param_type = str(parameters[0].get("type", "string")) if parameters else "string"
    return_type = str(test.get("return_type", "string"))

    parse_expr = _param_type_parse_expr(param_type)
    format_expr = _return_type_format_expr(return_type)
    input_repr = json.dumps(input_text, ensure_ascii=False)
    expected_repr = json.dumps(expected_output, ensure_ascii=False)

    test_body = (
        f'{_build_import_block(entry_name)}'
        f'    const _inputText = {input_repr};\n'
        f'    const _lines = _inputText.split("\\n");\n'
        f'    const _outputLines = _lines.map(_line => {{\n'
        f'        const _parsed = {parse_expr};\n'
        f'        const _result = _fn(_parsed);\n'
        f'        return {format_expr};\n'
        f'    }});\n'
        f'    const _actual = _outputLines.join("\\n");\n'
        f'    const _expected = {expected_repr};\n'
        f'    const _passed = _actual === _expected;\n'
        f'    return [_passed, _actual, _expected];\n'
    )

    full_source = make_javascript_test_file(test_id, test_body)
    filename = f"test_{index:02d}.js"
    return GeneratedTestArtifact(filename, full_source)

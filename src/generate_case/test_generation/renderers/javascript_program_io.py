import json
from typing import Any, Dict

from ..models import GeneratedTestArtifact
from .base import make_javascript_test_file


def render(test: Dict[str, Any]) -> GeneratedTestArtifact:
    test_id = str(test["test_id"])
    io_case = test.get("io_case", {})
    input_text = str(io_case.get("input_text", ""))
    expected_output = str(io_case.get("expected_output_text", ""))

    input_repr = json.dumps(input_text, ensure_ascii=False)
    expected_repr = json.dumps(expected_output, ensure_ascii=False)

    test_body = (
        '    const cp = require("child_process");\n'
        '    const path = require("path");\n'
        '    const fs = require("fs");\n'
        '    const codeDir = "/workspace/code";\n'
        '    const codeFile = fs.readdirSync(codeDir).find(f => fs.statSync(path.join(codeDir, f)).isFile());\n'
        f'    const result = cp.spawnSync("node", [path.join(codeDir, codeFile)], {{\n'
        f'        input: {input_repr},\n'
        f'        encoding: "utf-8",\n'
        f'        timeout: 30000,\n'
        f'    }});\n'
        f'    const actual = (result.stdout || "").replace(/\\\\r\\\\n/g, "\\\\n").trim();\n'
        f'    const expected = {expected_repr};\n'
        f'    const passed = result.status === 0 && actual === expected;\n'
        f'    return [passed, actual, expected];\n'
    )

    full_source = make_javascript_test_file(test_id, test_body)
    filename = f"test_{test_id}.js"
    return GeneratedTestArtifact(filename, full_source)

from typing import Any, Dict

from ..models import GeneratedTestArtifact
from .base import make_python_test_file


def render(test: Dict[str, Any]) -> GeneratedTestArtifact:
    test_id = str(test["test_id"])
    description = str(test.get("description", ""))
    io_case = test.get("io_case", {})
    input_text = str(io_case.get("input_text", ""))
    expected_output = str(io_case.get("expected_output_text", ""))

    import_repr = repr(input_text)
    expected_repr = repr(expected_output)

    test_body = (
        '    import subprocess, sys\n'
        '    from pathlib import Path\n'
        f'    _code_file = next(f for f in sorted((Path("/workspace/code")).iterdir()) if f.is_file())\n'
        f'    _result = subprocess.run(\n'
        f'        [sys.executable, str(_code_file)],\n'
        f'        input={import_repr},\n'
        f'        capture_output=True,\n'
        f'        text=True,\n'
        f'        timeout=30,\n'
        f'    )\n'
        f'    _actual = _result.stdout.replace("\\\\r\\\\n", "\\\\n").rstrip()\n'
        f'    _expected = {expected_repr}\n'
        f'    _passed = _result.returncode == 0 and _actual == _expected\n'
        f'    return _passed, _actual, _expected\n'
    )

    full_source = make_python_test_file(test_id, test_body)
    filename = f"test_{test_id}.py"
    return GeneratedTestArtifact(filename, full_source)

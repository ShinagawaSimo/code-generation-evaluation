import shutil
from pathlib import Path
from typing import Dict, Optional


def _require_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def build_python(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tool = _require_tool("python")
    if not tool:
        return {"error": "python_not_found"}
    return {
        "build_command": [tool, "-m", "py_compile", str(source_path)],
        "run_command": [tool, str(source_path)],
        "output_path": "",
    }

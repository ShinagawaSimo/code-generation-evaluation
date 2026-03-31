import shutil
from pathlib import Path
from typing import Dict, Optional


def _require_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def build_c(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tool = _require_tool("gcc")
    if not tool:
        return {"error": "gcc_not_found"}
    return {
        "build_command": [tool, str(source_path), "-o", str(output_path)],
        "run_command": [str(output_path)],
        "output_path": str(output_path),
    }


def build_cpp(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tool = _require_tool("g++")
    if not tool:
        return {"error": "g++_not_found"}
    return {
        "build_command": [tool, str(source_path), "-o", str(output_path)],
        "run_command": [str(output_path)],
        "output_path": str(output_path),
    }

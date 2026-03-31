import shutil
from pathlib import Path
from typing import Dict, Optional


def _require_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def build_go(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tool = _require_tool("go")
    if not tool:
        return {"error": "go_not_found"}
    return {
        "build_command": [tool, "build", "-o", str(output_path), str(source_path)],
        "run_command": [str(output_path)],
        "output_path": str(output_path),
    }

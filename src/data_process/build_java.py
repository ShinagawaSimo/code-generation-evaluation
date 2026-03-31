import shutil
from pathlib import Path
from typing import Dict, Optional


def _require_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def build_java(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tool = _require_tool("javac")
    if not tool:
        return {"error": "javac_not_found"}
    class_name = source_path.stem
    return {
        "build_command": [tool, str(source_path)],
        "run_command": ["java", "-cp", str(work_dir), class_name],
        "output_path": str(work_dir / f"{class_name}.class"),
    }

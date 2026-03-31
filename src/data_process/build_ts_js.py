import shutil
from pathlib import Path
from typing import Dict, Optional


def _require_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def build_javascript(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tool = _require_tool("node")
    if not tool:
        return {"error": "node_not_found"}
    return {
        "build_command": [tool, "--check", str(source_path)],
        "run_command": [tool, str(source_path)],
        "output_path": "",
    }


def build_typescript(source_path: Path, output_path: Path, work_dir: Path) -> Dict[str, object]:
    tsc = _require_tool("tsc")
    node = _require_tool("node")
    if not tsc or not node:
        return {"error": "tsc_or_node_not_found"}
    compiled_js = work_dir / f"{source_path.stem}.js"
    return {
        "build_command": [tsc, "--outDir", str(work_dir), str(source_path)],
        "run_command": [node, str(compiled_js)],
        "output_path": "",
    }

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


LANGUAGE_ALIASES = {
    "c": "c",
    "c89": "c",
    "c99": "c",
    "c11": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "python": "python",
    "py": "python",
    "java": "java",
    "rust": "rust",
    "rs": "rust",
    "go": "go",
    "golang": "go",
    "typescript": "typescript",
    "ts": "typescript",
    "javascript": "javascript",
    "js": "javascript",
}


CODE_FENCE_LANGS = {
    "c",
    "cpp",
    "c++",
    "python",
    "py",
    "java",
    "rust",
    "rs",
    "go",
    "typescript",
    "ts",
    "javascript",
    "js",
}


def normalize_language(language: str) -> str:
    """
    Normalize language names to supported canonical identifiers.
    language: input language name or alias.
    """
    key = (language or "").strip().lower()
    return LANGUAGE_ALIASES.get(key, key)


def extract_code(raw_output: str) -> str:
    """
    Extract source code from model output.
    raw_output: model output that may include CODE_START/CODE_END or code fences.
    """
    if "CODE_START" in raw_output and "CODE_END" in raw_output:
        start = raw_output.find("CODE_START") + len("CODE_START")
        end = raw_output.find("CODE_END", start)
        if end > start:
            return raw_output[start:end].strip()
    if "ACTION:" in raw_output and "INPUT:" in raw_output:
        return ""
    if "```" not in raw_output:
        return raw_output.strip()
    parts = raw_output.split("```")
    if len(parts) < 3:
        return raw_output.strip()
    content = parts[1].strip("\n")
    lines = content.splitlines()
    if lines:
        first = lines[0].strip().lower()
        if first in CODE_FENCE_LANGS:
            return "\n".join(lines[1:]).strip()
    return content.strip()


def _sanitize_case_id(case_id: Optional[str]) -> str:
    """
    Convert a case identifier into a safe filename suffix.
    case_id: raw case identifier used for naming output files.
    """
    if not case_id:
        return "case"
    digits = "".join(ch for ch in str(case_id) if ch.isdigit())
    if digits:
        return digits
    cleaned = re.sub(r"[^0-9A-Za-z]+", "_", str(case_id)).strip("_")
    return cleaned or "case"


def default_source_name(language: str, case_id: Optional[str] = None) -> str:
    """
    Build a default source filename using language and case id.
    language: normalized language name.
    case_id: case identifier used as filename suffix.
    """
    normalized = normalize_language(language)
    suffix = _sanitize_case_id(case_id)
    return {
        "c": f"main_{suffix}.c",
        "cpp": f"main_{suffix}.cpp",
        "python": f"main_{suffix}.py",
        "java": f"Main_{suffix}.java",
        "rust": f"main_{suffix}.rs",
        "go": f"main_{suffix}.go",
        "typescript": f"main_{suffix}.ts",
        "javascript": f"main_{suffix}.js",
    }.get(normalized, f"main_{suffix}.txt")


def default_output_name() -> str:
    """
    Provide a default executable output name by OS.
    """
    return "program.exe" if os.name == "nt" else "program"


def write_source_file(workspace: Path, filename: str, code: str) -> Path:
    """
    Write source code into a file under the workspace.
    workspace: target directory to place the source file.
    filename: source file name.
    code: source code content.
    """
    workspace.mkdir(parents=True, exist_ok=True)
    source_path = workspace / filename
    source_path.write_text(code, encoding="utf-8")
    return source_path


def _require_tool(tool_name: str) -> Optional[str]:
    """
    Resolve a required build tool path or return None.
    tool_name: executable name to locate in PATH.
    """
    return shutil.which(tool_name)


def build_executable(
    language: str,
    raw_output: str,
    workspace: str,
    source_name: Optional[str] = None,
    output_name: Optional[str] = None,
    case_id: Optional[str] = None,
) -> Dict[str, object]:
    """
    Compile or prepare runnable code for the given language.
    language: target programming language.
    raw_output: model-generated output containing source code.
    workspace: directory to write source and build artifacts.
    source_name: optional explicit source filename.
    output_name: optional explicit output binary name.
    case_id: case identifier to suffix filenames.
    """
    normalized = normalize_language(language)
    work_dir = Path(workspace).resolve()
    code = extract_code(raw_output)
    if not code:
        return {
            "success": False,
            "error": "empty_model_output",
            "workspace": str(work_dir),
        }
    src_name = source_name or default_source_name(normalized, case_id=case_id)
    out_name = output_name or default_output_name()
    source_path = write_source_file(work_dir, src_name, code)
    output_path = work_dir / out_name

    build_command: List[str] = []
    run_command: List[str] = []

    if normalized == "c":
        tool = _require_tool("gcc")
        if not tool:
            return {"success": False, "error": "gcc_not_found", "source_path": str(source_path)}
        build_command = [tool, str(source_path), "-o", str(output_path)]
        run_command = [str(output_path)]
    elif normalized == "cpp":
        tool = _require_tool("g++")
        if not tool:
            return {"success": False, "error": "g++_not_found", "source_path": str(source_path)}
        build_command = [tool, str(source_path), "-o", str(output_path)]
        run_command = [str(output_path)]
    elif normalized == "rust":
        tool = _require_tool("rustc")
        if not tool:
            return {"success": False, "error": "rustc_not_found", "source_path": str(source_path)}
        build_command = [tool, str(source_path), "-o", str(output_path)]
        run_command = [str(output_path)]
    elif normalized == "go":
        tool = _require_tool("go")
        if not tool:
            return {"success": False, "error": "go_not_found", "source_path": str(source_path)}
        build_command = [tool, "build", "-o", str(output_path), str(source_path)]
        run_command = [str(output_path)]
    elif normalized == "java":
        tool = _require_tool("javac")
        if not tool:
            return {"success": False, "error": "javac_not_found", "source_path": str(source_path)}
        build_command = [tool, str(source_path)]
        class_name = source_path.stem
        run_command = ["java", "-cp", str(work_dir), class_name]
        output_path = work_dir / f"{class_name}.class"
    elif normalized == "python":
        tool = _require_tool("python")
        if not tool:
            return {"success": False, "error": "python_not_found", "source_path": str(source_path)}
        build_command = [tool, "-m", "py_compile", str(source_path)]
        run_command = [tool, str(source_path)]
    elif normalized == "javascript":
        tool = _require_tool("node")
        if not tool:
            return {"success": False, "error": "node_not_found", "source_path": str(source_path)}
        build_command = [tool, "--check", str(source_path)]
        run_command = [tool, str(source_path)]
    elif normalized == "typescript":
        tsc = _require_tool("tsc")
        node = _require_tool("node")
        if not tsc or not node:
            return {
                "success": False,
                "error": "tsc_or_node_not_found",
                "source_path": str(source_path),
            }
        build_command = [tsc, "--outDir", str(work_dir), str(source_path)]
        compiled_js = work_dir / f"{source_path.stem}.js"
        run_command = [node, str(compiled_js)]
    else:
        return {
            "success": False,
            "error": "unsupported_language",
            "language": normalized,
            "source_path": str(source_path),
        }

    result = subprocess.run(
        build_command,
        cwd=str(work_dir),
        capture_output=True,
        text=True,
    )
    success = result.returncode == 0
    return {
        "success": success,
        "workspace": str(work_dir),
        "language": normalized,
        "source_path": str(source_path),
        "output_path": str(output_path) if output_path.exists() else "",
        "build_command": build_command,
        "run_command": run_command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }

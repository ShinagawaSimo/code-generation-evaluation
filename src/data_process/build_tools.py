from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .build_c_cpp import build_c, build_cpp
from .build_go import build_go
from .build_java import build_java
from .build_python import build_python
from .build_rust import build_rust
from .build_ts_js import build_javascript, build_typescript

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


def _build_env() -> Dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
    }


def _select_builder(language: str):
    return {
        "c": build_c,
        "cpp": build_cpp,
        "rust": build_rust,
        "go": build_go,
        "java": build_java,
        "python": build_python,
        "javascript": build_javascript,
        "typescript": build_typescript,
    }.get(language)


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

    builder = _select_builder(normalized)
    if not builder:
        return {
            "success": False,
            "error": "unsupported_language",
            "language": normalized,
            "source_path": str(source_path),
        }
    plan = builder(source_path, output_path, work_dir)
    if "error" in plan:
        return {"success": False, "error": plan["error"], "source_path": str(source_path)}
    build_command = plan.get("build_command", [])
    run_command = plan.get("run_command", [])
    planned_output = plan.get("output_path")
    if planned_output:
        output_path = Path(planned_output)

    build_timeout = int(os.getenv("BUILD_TIMEOUT_SECONDS", "30"))
    try:
        result = subprocess.run(
            build_command,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=build_timeout,
            env=_build_env(),
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "build_timeout",
            "workspace": str(work_dir),
            "language": normalized,
            "source_path": str(source_path),
            "output_path": "",
            "build_command": build_command,
            "run_command": run_command,
        }
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

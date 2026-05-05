import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _rewrite_checker(path: Path, language: str, entry_name: str) -> None:
    if not path.exists():
        return
    templates = {
        ".py": f"from solution import {entry_name}\n\n# Auto-adapted checker placeholder\n",
        ".js": f"const {{ {entry_name} }} = require('./solution');\n\n// Auto-adapted checker placeholder\n",
        ".ts": f"import {{ {entry_name} }} from './solution';\n\n// Auto-adapted checker placeholder\n",
    }
    content = templates.get(path.suffix.lower())
    if content is not None:
        path.write_text(content, encoding="utf-8")


def _adapt_function_call_spec(spec: Dict[str, Any], implemented_interface: Dict[str, Any]) -> bool:
    if spec.get("execution_mode") != "function_call":
        return False
    target_signature = dict(spec.get("target_signature", {}))
    target_signature["entry_name"] = str(implemented_interface.get("entry_name", ""))
    target_signature["parameters"] = list(implemented_interface.get("parameters", []))
    target_signature["return_type"] = str(implemented_interface.get("return_type", ""))
    spec["target_signature"] = target_signature

    function_contract = dict(spec.get("function_contract", {}))
    function_contract["call_style"] = "positional_only"
    function_contract["parameter_order"] = [
        str(item.get("name", ""))
        for item in implemented_interface.get("parameters", [])
        if isinstance(item, dict) and item.get("name")
    ]
    function_contract["notes"] = list(implemented_interface.get("notes", []))
    spec["function_contract"] = function_contract
    return True


def adapt_tests_for_interface(
    task_id: str,
    language: str,
    implemented_interface: Dict[str, Any],
    source_tests_root: str,
    adapted_tests_root: str,
) -> Dict[str, Any]:
    source_task_dir = Path(source_tests_root) / task_id
    if not source_task_dir.exists():
        return {
            "adapted_tests_dir": "",
            "updated_point_count": 0,
            "adapted_files": [],
            "warnings": [f"source test directory not found: {source_task_dir}"],
        }

    target_task_dir = Path(adapted_tests_root) / task_id
    if target_task_dir.exists():
        shutil.rmtree(target_task_dir)
    shutil.copytree(source_task_dir, target_task_dir)

    adapted_files: List[str] = []
    updated_point_count = 0
    entry_name = str(implemented_interface.get("entry_name", ""))

    for spec_path in sorted(target_task_dir.rglob("spec.json")):
        spec = _load_json(spec_path)
        changed = _adapt_function_call_spec(spec, implemented_interface)
        if changed:
            _save_json(spec_path, spec)
            adapted_files.append(str(spec_path))
            updated_point_count += 1

        function_cases_path = spec_path.parent / "function_cases.json"
        if changed and function_cases_path.exists():
            function_cases = _load_json(function_cases_path)
            function_cases["target_signature"] = spec.get("target_signature", {})
            _save_json(function_cases_path, function_cases)
            adapted_files.append(str(function_cases_path))

        if changed:
            for pattern in ["checker.py", "checker.js", "checker.ts", "Checker.java", "checker.go", "checker.rs", "checker.c", "checker.cpp"]:
                checker_path = spec_path.parent / pattern
                if checker_path.exists():
                    _rewrite_checker(checker_path, language, entry_name)
                    adapted_files.append(str(checker_path))

    return {
        "adapted_tests_dir": str(target_task_dir),
        "updated_point_count": updated_point_count,
        "total_point_count": len(list(target_task_dir.glob("point_*"))),
        "adapted_files": adapted_files,
        "warnings": [],
    }

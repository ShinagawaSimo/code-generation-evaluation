import json
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_points(points: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for p in points:
        pid = p.get("point_id", "")
        text = p.get("point_text", "")
        cat = p.get("category", "")
        explicit = p.get("is_explicit_in_original", True)
        flag = "[E]" if explicit else "[I]"
        lines.append(f"    {flag} {pid} ({cat}): {text}")
    return "\n".join(lines)


def _format_test_specs(specs: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for s in specs:
        pid = s.get("point_id", "")
        text = s.get("point_text", "")
        kind = s.get("test_kind", "")
        lines.append(f"    {pid} ({kind}): {text}")
    return "\n".join(lines)


def _format_reference_implementations(implementations: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for impl in implementations:
        aid = impl.get("approach_id", "")
        name = impl.get("approach_name", "")
        desc = impl.get("description", "")
        file_path = impl.get("code_file_path", "")
        lines.append(f"    [{aid}] {name}")
        lines.append(f"          description: {desc}")
        lines.append(f"          file: {file_path}")
    return "\n".join(lines)


def generate_case_summary(
    task_id: str,
    spec_result_path: str,
    test_result_path: str,
    reference_code_result_path: str,
    summary_dir: str,
) -> str:
    spec = _load_json(Path(spec_result_path)) if spec_result_path else {}
    test = _load_json(Path(test_result_path)) if test_result_path else {}
    ref = _load_json(Path(reference_code_result_path)) if reference_code_result_path else {}

    lines: List[str] = []
    lines.append("=" * 64)
    lines.append(f"Case Summary: {task_id}")
    lines.append("=" * 64)

    lines.append("")
    lines.append("[Original Requirement]")
    lines.append("-" * 64)
    lines.append(spec.get("original_requirement_text", "(not available)"))

    lines.append("")
    lines.append("[Requirement Points]")
    lines.append("-" * 64)
    points = spec.get("requirement_points", [])
    if points:
        lines.append(_format_points(points))
    else:
        lines.append("    (not available)")

    lines.append("")
    lines.append("[Test Specifications]")
    lines.append("-" * 64)
    test_specs = test.get("point_specs", [])
    if test_specs:
        lines.append(_format_test_specs(test_specs))
    else:
        lines.append("    (not available)")

    lines.append("")
    lines.append("[Test Generated Files]")
    lines.append("-" * 64)
    generated_files = test.get("generated_files", [])
    if generated_files:
        for gf in generated_files:
            lines.append(f"    {gf}")
    else:
        lines.append("    (not available)")

    lines.append("")
    lines.append("[Reference Implementations]")
    lines.append("-" * 64)
    implementations = ref.get("reference_implementations", [])
    if implementations:
        lines.append(_format_reference_implementations(implementations))
    else:
        lines.append("    (not available)")

    lines.append("")
    lines.append("=" * 64)
    lines.append(f"End of Summary: {task_id}")
    lines.append("=" * 64)

    summary_text = "\n".join(lines) + "\n"

    summary_path = Path(summary_dir) / f"{task_id}.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary_text, encoding="utf-8")
    return str(summary_path)

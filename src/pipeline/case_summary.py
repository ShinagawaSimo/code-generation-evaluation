import json
from pathlib import Path
from typing import Any, Dict


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def generate_case_summary(
    task_id: str,
    spec_result_path: str,
    test_result_path: str,
    reference_code_result_path: str,
    summary_dir: str,
) -> str:
    spec = _load_json(Path(spec_result_path))
    test = _load_json(Path(test_result_path))
    ref = _load_json(Path(reference_code_result_path))

    summary = {
        "task_id": task_id,
        "original_requirement_text": spec["original_requirement_text"],
        "requirement_points": spec["requirement_points"],
        "test_specs": test["point_specs"],
        "test_generated_files": test["generated_files"],
        "reference_implementations": ref["reference_implementations"],
    }

    summary_path = Path(summary_dir) / f"{task_id}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(summary_path)

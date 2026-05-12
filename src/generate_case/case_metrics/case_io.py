import json
from pathlib import Path
from typing import Any, Dict, List

from .models import CaseMetricsResult


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str, data: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_case_paths(cases_dir: str, case_glob: str) -> List[Path]:
    base = Path(cases_dir)
    return sorted(path for path in base.glob(case_glob) if path.is_file())


list_result_paths = list_case_paths


def build_result_path(results_dir: str, task_id: str) -> Path:
    return Path(results_dir) / f"{task_id}.json"


def save_case_metrics_result(result_path: str, result: CaseMetricsResult) -> None:
    save_json(result_path, result.to_dict())

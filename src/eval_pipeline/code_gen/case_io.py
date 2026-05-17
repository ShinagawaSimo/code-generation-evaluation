import json
from pathlib import Path
from typing import Any, Dict, List

from shared.case_text import load_case

from .models import CodeGenerationRequest, CodeGenerationResult


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str, data: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_case_paths(cases_dir: str, case_glob: str) -> List[Path]:
    base = Path(cases_dir)
    return sorted(path for path in base.glob(case_glob) if path.is_file())


def _load_sidecar_defaults(case_path: Path) -> Dict[str, Any]:
    sidecar_path = case_path.with_suffix(".meta.json")
    if not sidecar_path.exists():
        return {}
    return json.loads(sidecar_path.read_text(encoding="utf-8"))


def load_code_generation_request(case_path: str, defaults: Dict[str, Any] | None = None) -> CodeGenerationRequest:
    path = Path(case_path)
    defaults = {**(defaults or {}), **_load_sidecar_defaults(path)}
    case_data = load_case(path)
    return CodeGenerationRequest(
        task_id=str(defaults.get("task_id") or case_data["task_id"]),
        case_basename=path.stem,
        language=case_data["language"],
        original_requirement_text=case_data["body"],
        acceptance_standard=case_data.get("acceptance_standard") or dict(defaults.get("acceptance_standard", {})),
        relevant_code=str(case_data.get("relevant_code", "")),
    )


def build_result_path(results_dir: str, task_id: str) -> Path:
    return Path(results_dir) / f"{task_id}.json"


def save_code_generation_result(result_path: str, result: CodeGenerationResult) -> None:
    save_json(result_path, result.to_dict())

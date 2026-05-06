import json
from pathlib import Path
from typing import Any, Dict, List

from shared.case_text import parse_case_text

from .models import CaseSpecRequest, CaseSpecResult


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


def load_case_spec_request(case_path: str, defaults: Dict[str, Any] | None = None) -> CaseSpecRequest:
    path = Path(case_path)
    defaults = {**(defaults or {}), **_load_sidecar_defaults(path)}
    parsed_case = parse_case_text(
        path.read_text(encoding="utf-8"),
        str(defaults.get("language", "")),
    )
    return CaseSpecRequest(
        task_id=str(defaults.get("task_id") or path.stem),
        original_requirement_text=parsed_case["body"],
        language=parsed_case["language"],
        extra_context=dict(defaults.get("extra_context", {})),
        allow_optional_features=bool(defaults.get("allow_optional_features", True)),
        preserve_user_constraints=bool(defaults.get("preserve_user_constraints", True)),
        output_language=str(defaults.get("output_language", "zh-CN")),
        classification_labels=list(defaults.get("classification_labels", []))
        or [
            "basic_function",
            "implicit_function",
            "optional_function",
            "basic_non_function",
            "optional_non_function",
        ],
    )


def build_result_path(results_dir: str, task_id: str) -> Path:
    return Path(results_dir) / f"{task_id}.json"


def save_result(result_path: str, result: CaseSpecResult) -> None:
    save_json(result_path, result.to_dict())

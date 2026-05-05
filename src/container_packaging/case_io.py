import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .models import ContainerPackagingResult


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str, data: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_result_paths(results_dir: str, result_glob: str) -> List[Path]:
    base = Path(results_dir)
    return sorted(path for path in base.glob(result_glob) if path.is_file())


def build_result_path(results_dir: str, task_id: str) -> Path:
    return Path(results_dir) / f"{task_id}.json"


def copy_tree(source_dir: str, target_dir: str) -> List[str]:
    source = Path(source_dir)
    target = Path(target_dir)
    copied: List[str] = []
    if not source.exists():
        return copied
    for path in source.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied.append(str(destination))
    return copied


def save_container_packaging_result(result_path: str, result: ContainerPackagingResult) -> None:
    save_json(result_path, result.to_dict())

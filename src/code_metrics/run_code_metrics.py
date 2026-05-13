import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_metrics.case_io import (
    build_result_path,
    list_result_paths,
    load_json,
    save_code_metrics_result,
)
from code_metrics.service import evaluate_code_metrics
from shared.file_utils import clear_output_files


def run_code_metrics(task_id: str | None = None) -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "code_metrics.json"))

    codegen_paths = list_result_paths(
        str(project_root / stage_config["code_generation_results_dir"]),
        str(stage_config["code_generation_result_glob"]),
    )
    codgen_results = {path.stem: load_json(str(path)) for path in codegen_paths}

    exec_paths = list_result_paths(
        str(project_root / stage_config["code_execution_results_dir"]),
        str(stage_config["code_execution_result_glob"]),
    )
    exec_results = {path.stem: load_json(str(path)) for path in exec_paths}

    ref_results: dict[str, dict] = {}
    ref_base = project_root / stage_config["reference_code_generation_results_dir"]
    for case_dir in sorted(ref_base.iterdir()):
        if not case_dir.is_dir():
            continue
        tid = case_dir.name
        ref_dir = case_dir / "reference"
        if not ref_dir.is_dir():
            continue
        json_path = ref_dir / f"{tid}.json"
        if json_path.exists():
            ref_results[tid] = load_json(str(json_path))
        else:
            implementations: list[dict] = []
            for py_file in sorted(ref_dir.glob("*.py")):
                stem = py_file.stem
                parts = stem.split("_", 1)
                approach_id = parts[1] if len(parts) > 1 else stem
                implementations.append({
                    "approach_id": approach_id,
                    "approach_name": approach_id,
                    "code_file_path": str(py_file),
                })
            if implementations:
                ref_results[tid] = {
                    "task_id": tid,
                    "reference_implementations": implementations,
                }

    all_task_ids = (
        set(codgen_results.keys()) & set(exec_results.keys()) & set(ref_results.keys())
    )
    if task_id:
        if task_id not in all_task_ids:
            raise ValueError(f"Task {task_id} not found in all result sets")
        all_task_ids = {task_id}
    print(f"[code_metrics] task_ids={len(all_task_ids)}")

    results_dir = str(project_root / stage_config["results_dir"])
    execution_artifacts_dir = str(project_root / stage_config["code_execution_artifacts_dir"])

    for task_id in sorted(all_task_ids):
        print(f"[code_metrics] task_id={task_id}")
        clear_output_files(results_dir, [f"{task_id}.json"])
        result = evaluate_code_metrics(
            task_id=task_id,
            code_gen_result=codgen_results[task_id],
            exec_result=exec_results[task_id],
            ref_result=ref_results[task_id],
        )
        save_code_metrics_result(str(build_result_path(results_dir, task_id)), result)
        passed = result.test_results.get("passed", 0)
        failed = result.test_results.get("failed", 0)
        pass_rate = result.test_results.get("pass_rate", 0.0)
        print(f"[code_metrics] task_id={task_id} passed={passed} failed={failed} pass_rate={pass_rate}")

    print("[code_metrics] complete")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run code metrics evaluation")
    parser.add_argument("--task-id", help="Process a single case by task ID")
    args = parser.parse_args()
    run_code_metrics(task_id=args.task_id)

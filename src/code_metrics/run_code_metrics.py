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


def run_code_metrics() -> None:
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

    ref_paths = list_result_paths(
        str(project_root / stage_config["reference_code_generation_results_dir"]),
        str(stage_config["reference_code_generation_result_glob"]),
    )
    ref_results = {path.stem: load_json(str(path)) for path in ref_paths}

    all_task_ids = (
        set(codgen_results.keys()) & set(exec_results.keys()) & set(ref_results.keys())
    )
    print(f"[code_metrics] task_ids={len(all_task_ids)}")

    results_dir = str(project_root / stage_config["results_dir"])
    execution_artifacts_dir = str(project_root / stage_config["code_execution_artifacts_dir"])

    for task_id in sorted(all_task_ids):
        print(f"[code_metrics] task_id={task_id}")
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
    run_code_metrics()

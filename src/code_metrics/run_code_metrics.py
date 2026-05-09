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

    codegen_paths = {
        p.stem: p
        for p in list_result_paths(
            str(project_root / stage_config["code_generation_results_dir"]),
            str(stage_config["code_generation_result_glob"]),
        )
    }
    exec_paths = {
        p.stem: p
        for p in list_result_paths(
            str(project_root / stage_config["container_execution_results_dir"]),
            str(stage_config["container_execution_result_glob"]),
        )
    }
    ref_paths = {
        p.stem: p
        for p in list_result_paths(
            str(project_root / stage_config["reference_code_generation_results_dir"]),
            str(stage_config["reference_code_generation_result_glob"]),
        )
    }
    spec_paths = {
        p.stem: p
        for p in list_result_paths(
            str(project_root / stage_config["case_spec_generation_results_dir"]),
            str(stage_config["case_spec_generation_result_glob"]),
        )
    }
    testgen_paths = {
        p.stem: p
        for p in list_result_paths(
            str(project_root / stage_config["test_generation_results_dir"]),
            str(stage_config["test_generation_result_glob"]),
        )
    }

    results_dir = str(project_root / stage_config["results_dir"])
    execution_artifacts_dir = str(project_root / stage_config["container_execution_artifacts_dir"])

    all_task_ids = (
        set(codegen_paths.keys())
        & set(exec_paths.keys())
        & set(ref_paths.keys())
        & set(spec_paths.keys())
        & set(testgen_paths.keys())
    )
    total_cases = len(all_task_ids)
    print(f"[code_metrics] start total_cases={total_cases}")

    for case_index, task_id in enumerate(sorted(all_task_ids), start=1):
        print(f"[code_metrics] case {case_index}/{total_cases} task={task_id}")
        code_gen_result = load_json(str(codegen_paths[task_id]))
        exec_result = load_json(str(exec_paths[task_id]))
        ref_result = load_json(str(ref_paths[task_id]))
        spec_result = load_json(str(spec_paths[task_id]))
        test_gen_result = load_json(str(testgen_paths[task_id]))

        result = evaluate_code_metrics(
            task_id=task_id,
            code_gen_result=code_gen_result,
            exec_result=exec_result,
            ref_result=ref_result,
            spec_result=spec_result,
            test_gen_result=test_gen_result,
            execution_artifacts_dir=execution_artifacts_dir,
        )
        save_code_metrics_result(str(build_result_path(results_dir, task_id)), result)
        print(f"[code_metrics] done task={task_id} result={build_result_path(results_dir, task_id)}")
    print("[code_metrics] complete")


if __name__ == "__main__":
    run_code_metrics()

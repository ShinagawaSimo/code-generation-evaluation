import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from container_execution.case_io import (
    build_result_path,
    list_result_paths,
    load_json,
    save_container_execution_result,
)
from container_execution.service import execute_container


def run_container_execution() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "container_execution.json"))
    packaging_results_dir = str(project_root / stage_config["container_packaging_results_dir"])
    packaging_result_glob = str(stage_config["container_packaging_result_glob"])
    results_dir = str(project_root / stage_config["results_dir"])
    logs_dir = str(project_root / stage_config["logs_dir"])
    artifacts_dir = str(project_root / stage_config["artifacts_dir"])
    execution_config = dict(stage_config.get("execution_config", {}))

    packaging_result_paths = list_result_paths(packaging_results_dir, packaging_result_glob)
    total_cases = len(packaging_result_paths)
    print(f"[container_execution] start total_cases={total_cases}")

    for case_index, packaging_result_path in enumerate(packaging_result_paths, start=1):
        print(f"[container_execution] case {case_index}/{total_cases} source={packaging_result_path}")
        packaging_result = load_json(str(packaging_result_path))
        task_id = str(packaging_result.get("task_id", ""))
        print(f"[container_execution] task={task_id} container_dir={packaging_result.get('container_dir', '')}")
        result = execute_container(
            packaging_result=packaging_result,
            execution_config=execution_config,
            logs_dir=logs_dir,
            artifacts_dir=artifacts_dir,
        )
        save_container_execution_result(str(build_result_path(results_dir, task_id)), result)
        print(
            f"[container_execution] done task={task_id} "
            f"environment_ready={result.environment_ready} "
            f"image_build_success={result.image_build_success} "
            f"compile_success={result.compile_success} "
            f"run_success={result.run_success} "
            f"tests_success={result.tests_success}"
        )
        if result.failure_message:
            print(f"[container_execution] failure task={task_id} message={result.failure_message}")
    print("[container_execution] complete")


if __name__ == "__main__":
    run_container_execution()

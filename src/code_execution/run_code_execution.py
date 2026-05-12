import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_execution.case_io import (
    build_result_path,
    list_result_paths,
    load_json,
    save_code_execution_result,
)
from code_execution.service import execute_code


def run_code_execution() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "code_execution.json"))

    codegen_results = {
        path.stem: load_json(str(path))
        for path in list_result_paths(
            str(project_root / stage_config["code_generation_results_dir"]),
            str(stage_config["code_generation_result_glob"]),
        )
    }

    results_dir = str(project_root / stage_config["results_dir"])
    generated_tests_dir = str(project_root / stage_config["generated_tests_dir"])
    container_output_dir = str(project_root / stage_config["container_output_dir"])
    logs_dir = str(project_root / stage_config["logs_dir"])
    artifacts_dir = str(project_root / stage_config["artifacts_dir"])
    execution_config = dict(stage_config.get("execution_config", {}))

    total_cases = len(codegen_results)
    print(f"[code_execution] start total_cases={total_cases}")

    for case_index, (task_id, codegen_result) in enumerate(codegen_results.items(), start=1):
        print(f"[code_execution] case {case_index}/{total_cases} task={task_id}")
        language = str(codegen_result.get("language", ""))
        result = execute_code(
            task_id=task_id,
            language=language,
            codegen_result=codegen_result,
            generated_tests_dir=generated_tests_dir,
            container_output_dir=container_output_dir,
            execution_config=execution_config,
            logs_dir=logs_dir,
            artifacts_dir=artifacts_dir,
        )
        save_code_execution_result(str(build_result_path(results_dir, task_id)), result)
        print(
            f"[code_execution] done task={task_id} "
            f"compile_success={result.compile_success} "
            f"tests_success={result.tests_success} "
            f"passed={result.passed_test_count} "
            f"failed={result.failed_test_count}"
        )
        if result.failure_message:
            print(f"[code_execution] failure task={task_id} message={result.failure_message}")
    print("[code_execution] complete")


if __name__ == "__main__":
    run_code_execution()

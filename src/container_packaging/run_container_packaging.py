import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from container_packaging.case_io import (
    build_result_path,
    list_result_paths,
    load_json,
    save_container_packaging_result,
)
from container_packaging.service import package_case_container


def run_container_packaging() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "container_packaging.json"))

    codegen_results = {
        path.stem: load_json(str(path))
        for path in list_result_paths(
            str(project_root / stage_config["code_generation_results_dir"]),
            str(stage_config["code_generation_result_glob"]),
        )
    }
    testgen_results = {
        path.stem: load_json(str(path))
        for path in list_result_paths(
            str(project_root / stage_config["test_generation_results_dir"]),
            str(stage_config["test_generation_result_glob"]),
        )
    }

    results_dir = str(project_root / stage_config["results_dir"])
    generated_tests_dir = str(project_root / stage_config["generated_tests_dir"])
    output_dir = str(project_root / stage_config["container_output_dir"])
    total_cases = len(codegen_results)
    print(f"[container_packaging] start total_cases={total_cases}")

    for case_index, (task_id, codegen_result) in enumerate(codegen_results.items(), start=1):
        print(f"[container_packaging] case {case_index}/{total_cases} task={task_id}")
        testgen_result = testgen_results.get(task_id, {"point_specs": [], "generated_files": []})
        result = package_case_container(
            task_id=task_id,
            language=str(codegen_result.get("language", "")),
            codegen_result=codegen_result,
            testgen_result=testgen_result,
            generated_tests_dir=generated_tests_dir,
            output_dir=output_dir,
        )
        save_container_packaging_result(str(build_result_path(results_dir, task_id)), result)
        print(f"[container_packaging] done task={task_id} context={result.container_dir}")
    print("[container_packaging] complete")


if __name__ == "__main__":
    run_container_packaging()

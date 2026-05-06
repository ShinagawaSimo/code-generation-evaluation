import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_generation.case_io import (
    build_case_output_dir,
    build_result_path,
    list_result_paths,
    load_json,
    save_test_generation_result,
)
from test_generation.service import generate_tests_for_case


def run_test_generation() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "test_generation.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))

    source_result_paths = list_result_paths(
        str(project_root / stage_config["case_spec_generation_results_dir"]),
        str(stage_config["case_spec_generation_result_glob"]),
    )
    results_dir = str(project_root / stage_config["results_dir"])
    generated_root_dir = str(project_root / stage_config["generated_tests_dir"])
    generation_config = dict(stage_config.get("generation_config", {}))
    total_cases = len(source_result_paths)
    print(f"[test_generation] start total_cases={total_cases}")

    for case_index, source_result_path in enumerate(source_result_paths, start=1):
        print(f"[test_generation] case {case_index}/{total_cases} source={source_result_path}")
        expansion_result = load_json(str(source_result_path))
        task_id = str(expansion_result.get("task_id", ""))
        output_dir = str(build_case_output_dir(generated_root_dir, task_id))
        print(f"[test_generation] task={task_id} output_dir={output_dir}")
        result = generate_tests_for_case(expansion_result, api_config, generation_config, output_dir)
        save_test_generation_result(str(build_result_path(results_dir, task_id)), result)
        print(
            f"[test_generation] done task={task_id} "
            f"point_specs={len(result.point_specs)} generated_files={len(result.generated_files)}"
        )
    print("[test_generation] complete")


if __name__ == "__main__":
    run_test_generation()

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_generation.case_io import (
    build_result_path,
    list_case_paths,
    load_code_generation_request,
    load_json,
    save_code_generation_result,
)
from code_generation.service import generate_code


def run_code_generation() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "code_generation.json"))
    api_config = load_json(str(project_root / "config" / "model_api_codegen.json"))

    case_paths = list_case_paths(
        str(project_root / stage_config["cases_dir"]),
        str(stage_config["case_glob"]),
    )
    case_defaults = dict(stage_config.get("case_defaults", {}))
    results_dir = str(project_root / stage_config["results_dir"])
    code_output_dir = str(project_root / stage_config["code_output_dir"])
    raw_output_dir = str(project_root / stage_config["raw_output_dir"])
    generation_config = dict(stage_config.get("generation_config", {}))
    for path_key in ["implemented_interface_dir", "source_tests_dir", "adapted_tests_dir"]:
        if generation_config.get(path_key):
            generation_config[path_key] = str(project_root / str(generation_config[path_key]))
    total_cases = len(case_paths)
    print(f"[code_generation] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        print(f"[code_generation] case {case_index}/{total_cases} path={case_path}")
        request = load_code_generation_request(str(case_path), defaults=case_defaults)
        print(f"[code_generation] task={request.task_id} language={request.language}")
        result = generate_code(request, api_config, generation_config, code_output_dir, raw_output_dir)
        save_code_generation_result(str(build_result_path(results_dir, request.task_id)), result)
        print(
            f"[code_generation] done task={request.task_id} "
            f"code={result.code_file_path} "
            f"interface={result.implemented_interface_path} "
            f"adapted_points={result.adaptation_summary.get('updated_point_count', 0)} "
            f"adapted_total={result.adaptation_summary.get('total_point_count', 0)}"
        )
    print("[code_generation] complete")


if __name__ == "__main__":
    run_code_generation()

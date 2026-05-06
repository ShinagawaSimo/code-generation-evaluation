import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_spec_generation.case_io import (
    build_result_path,
    list_case_paths,
    load_case_spec_request,
    load_json,
    save_result,
)
from case_spec_generation.prompting import get_case_spec_generation_prompt
from case_spec_generation.service import generate_case_spec


def run_case_spec_generation() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pipeline_config = load_json(str(project_root / "config" / "case_spec_generation.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))
    prompt_text = get_case_spec_generation_prompt(str(project_root / pipeline_config["prompt_path"]))

    case_paths = list_case_paths(
        str(project_root / pipeline_config["cases_dir"]),
        str(pipeline_config["case_glob"]),
    )
    case_defaults = dict(pipeline_config.get("case_defaults", {}))
    results_dir = str(project_root / pipeline_config["results_dir"])
    raw_output_dir = str(project_root / pipeline_config["raw_output_dir"])
    total_cases = len(case_paths)
    print(f"[case_spec_generation] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        print(f"[case_spec_generation] case {case_index}/{total_cases} path={case_path}")
        request = load_case_spec_request(str(case_path), defaults=case_defaults)
        print(f"[case_spec_generation] task={request.task_id} language={request.language}")
        result = generate_case_spec(request, api_config, prompt_text=prompt_text)
        save_result(str(build_result_path(results_dir, request.task_id)), result)
        print(
            f"[case_spec_generation] done task={request.task_id} points={len(result.requirement_points)} "
            f"result={build_result_path(results_dir, request.task_id)}"
        )
    print("[case_spec_generation] complete")


if __name__ == "__main__":
    run_case_spec_generation()

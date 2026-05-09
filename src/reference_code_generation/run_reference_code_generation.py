import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reference_code_generation.case_io import (
    build_result_path,
    list_result_paths,
    load_json,
    save_result,
)
from reference_code_generation.prompting import load_reference_code_prompt
from reference_code_generation.service import generate_reference_code


def run_reference_code_generation() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "reference_code_generation.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))
    prompt_text = load_reference_code_prompt(str(project_root / stage_config["prompt_path"]))

    source_paths = list_result_paths(
        str(project_root / stage_config["case_spec_generation_results_dir"]),
        str(stage_config["case_spec_generation_result_glob"]),
    )
    results_dir = str(project_root / stage_config["results_dir"])
    code_output_dir = str(project_root / stage_config["code_output_dir"])
    total_cases = len(source_paths)
    print(f"[reference_code_generation] start total_cases={total_cases}")

    for case_index, case_path in enumerate(source_paths, start=1):
        print(f"[reference_code_generation] case {case_index}/{total_cases} path={case_path}")
        expansion_result = load_json(str(case_path))
        task_id = str(expansion_result.get("task_id", ""))
        language = str(expansion_result.get("language", ""))
        original_requirement_text = str(expansion_result.get("original_requirement_text", ""))

        print(f"[reference_code_generation] task={task_id} language={language}")
        result = generate_reference_code(
            task_id=task_id,
            language=language,
            original_requirement_text=original_requirement_text,
            api_config=api_config,
            code_output_dir=code_output_dir,
            prompt_text=prompt_text,
        )
        save_result(str(build_result_path(results_dir, task_id)), result)
        print(f"[reference_code_generation] done task={task_id} result={build_result_path(results_dir, task_id)}")
    print("[reference_code_generation] complete")


if __name__ == "__main__":
    run_reference_code_generation()

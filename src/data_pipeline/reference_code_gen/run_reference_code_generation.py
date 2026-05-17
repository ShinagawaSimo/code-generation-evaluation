import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data_pipeline.reference_code_gen.case_io import load_json, save_result, build_result_path
from data_pipeline.reference_code_gen.prompting import load_reference_code_prompt
from data_pipeline.reference_code_gen.service import generate_reference_code
from data_pipeline.test_data_gen.case_io import list_case_paths
from shared.case_text import load_case


def run_reference_code_generation(task_id: str | None = None) -> None:
    project_root = Path(__file__).resolve().parents[3]
    stage_config = load_json(str(project_root / "config" / "generate_case.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))

    case_paths = list_case_paths(
        str(project_root / stage_config["cases_dir"]),
        str(stage_config["cases_glob"]),
    )
    if task_id:
        case_paths = [p for p in case_paths if p.stem == task_id]
        if not case_paths:
            raise ValueError(f"No case found for task_id: {task_id}")
    output_cases_dir = str(project_root / stage_config["output_cases_dir"])
    reference_code_prompt_text = load_reference_code_prompt(
        str(project_root / stage_config["reference_code_prompt_path"])
    )

    total_cases = len(case_paths)
    print(f"[reference_code_generation] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        task_id = case_path.stem
        print(f"[reference_code_generation] case {case_index}/{total_cases} task={task_id}")

        case_data = load_case(case_path)
        original_requirement_text = case_data["body"]
        language = case_data["language"]
        relevant_code = str(case_data.get("relevant_code", ""))

        case_output_dir = Path(output_cases_dir) / task_id
        code_output_dir = str(case_output_dir / "reference")

        reference_result = generate_reference_code(
            task_id=task_id,
            language=language,
            original_requirement_text=original_requirement_text,
            api_config=api_config,
            code_output_dir=code_output_dir,
            prompt_text=reference_code_prompt_text,
            relevant_code=relevant_code,
        )
        save_result(str(build_result_path(str(case_output_dir / "reference"), task_id)), reference_result)
        print(f"[reference_code_generation] task={task_id} done implementations={len(reference_result.implementations)}")

    print("[reference_code_generation] all cases complete")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run reference code generation")
    parser.add_argument("--task-id", help="Process a single case by task ID")
    args = parser.parse_args()
    run_reference_code_generation(task_id=args.task_id)

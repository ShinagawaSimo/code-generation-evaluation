import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from generate_case.test_generation.case_io import list_case_paths, load_json
from generate_case.test_generation.service import generate_tests_for_case
from shared.case_text import load_case
from shared.file_utils import clear_output_files


def run_test_generation(task_id: str | None = None) -> None:
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
    generation_config = dict(stage_config.get("generation_config", {}))

    total_cases = len(case_paths)
    print(f"[test_generation] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        task_id = case_path.stem
        print(f"[test_generation] case {case_index}/{total_cases} task={task_id}")

        case_data = load_case(case_path)
        original_requirement_text = case_data["body"]
        language = case_data["language"]
        relevant_code = str(case_data.get("relevant_code", ""))

        case_output_dir = Path(output_cases_dir) / task_id
        tests_dir = case_output_dir / "tests"
        clear_output_files(str(tests_dir), ["**/test_*.py", "**/manifest.json"])
        case_output_dir.mkdir(parents=True, exist_ok=True)

        test_result = generate_tests_for_case(
            task_id=task_id,
            original_requirement_text=original_requirement_text,
            language=language,
            api_config=api_config,
            generation_config=generation_config,
            tests_output_dir=str(case_output_dir / "tests"),
            relevant_code=relevant_code,
        )
        print(f"[test_generation] task={task_id} done files={len(test_result.generated_files)}")

    print("[test_generation] all cases complete")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run test generation")
    parser.add_argument("--task-id", help="Process a single case by task ID")
    args = parser.parse_args()
    run_test_generation(task_id=args.task_id)

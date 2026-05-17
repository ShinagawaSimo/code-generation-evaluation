import shutil
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data_pipeline.case_metrics.case_io import load_json, save_case_metrics_result
from data_pipeline.case_metrics.service import evaluate_case_metrics
from data_pipeline.reference_code_gen.prompting import load_reference_code_prompt
from data_pipeline.reference_code_gen.service import generate_reference_code
from data_pipeline.test_data_gen.case_io import build_result_path as build_test_result_path
from data_pipeline.test_data_gen.case_io import list_case_paths
from data_pipeline.test_data_gen.service import generate_tests_for_case
from shared.case_text import load_case


def run_generate_case(task_id: str | None = None) -> None:
    project_root = Path(__file__).resolve().parents[2]
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
    metric_config = dict(stage_config.get("metric_config", {}))
    generation_config = dict(stage_config.get("generation_config", {}))
    reference_code_prompt_text = load_reference_code_prompt(
        str(project_root / stage_config["reference_code_prompt_path"])
    )

    total_cases = len(case_paths)
    print(f"[generate_case] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        task_id = case_path.stem
        print(f"[generate_case] case {case_index}/{total_cases} task={task_id}")

        case_data = load_case(case_path)
        original_requirement_text = case_data["body"]
        language = case_data["language"]
        relevant_code = str(case_data.get("relevant_code", ""))

        case_output_dir = Path(output_cases_dir) / task_id
        case_output_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(str(case_path), str(case_output_dir / "original.json"))
        print(f"[generate_case] task={task_id} original.json saved")

        metrics_result = evaluate_case_metrics(
            task_id=task_id,
            original_requirement_text=original_requirement_text,
            api_config=api_config,
            metric_config=metric_config,
        )
        save_case_metrics_result(
            str(case_output_dir / "case_metrics.json"),
            metrics_result,
        )
        print(f"[generate_case] task={task_id} case_metrics done")

        test_result = generate_tests_for_case(
            task_id=task_id,
            original_requirement_text=original_requirement_text,
            language=language,
            api_config=api_config,
            generation_config=generation_config,
            tests_output_dir=str(case_output_dir / "tests"),
            relevant_code=relevant_code,
        )
        print(f"[generate_case] task={task_id} tests done files={len(test_result.generated_files)}")

        reference_result = generate_reference_code(
            task_id=task_id,
            language=language,
            original_requirement_text=original_requirement_text,
            api_config=api_config,
            code_output_dir=str(case_output_dir / "reference"),
            prompt_text=reference_code_prompt_text,
            relevant_code=relevant_code,
        )
        print(f"[generate_case] task={task_id} reference done implementations={len(reference_result.implementations)}")

        print(f"[generate_case] task={task_id} complete output={case_output_dir}")

    print("[generate_case] all cases complete")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run full generate_case pipeline")
    parser.add_argument("--task-id", help="Process a single case by task ID")
    args = parser.parse_args()
    run_generate_case(task_id=args.task_id)

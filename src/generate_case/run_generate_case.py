import shutil
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_case.case_metrics.case_io import load_json, save_case_metrics_result
from generate_case.case_metrics.service import evaluate_case_metrics
from generate_case.reference_code_generation.prompting import load_reference_code_prompt
from generate_case.reference_code_generation.service import generate_reference_code
from generate_case.test_generation.case_io import build_result_path as build_test_result_path
from generate_case.test_generation.case_io import list_case_paths
from generate_case.test_generation.service import generate_tests_for_case
from shared.case_text import parse_case_text


def run_generate_case() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "generate_case.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))

    case_paths = list_case_paths(
        str(project_root / stage_config["cases_dir"]),
        str(stage_config["cases_glob"]),
    )
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

        case_text = case_path.read_text(encoding="utf-8")
        parsed = parse_case_text(case_text, "python")
        original_requirement_text = parsed["body"]
        language = str(parsed.get("language", "python"))

        case_output_dir = Path(output_cases_dir) / task_id
        case_output_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(str(case_path), str(case_output_dir / "original.txt"))
        print(f"[generate_case] task={task_id} original.txt saved")

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
        )
        print(f"[generate_case] task={task_id} tests done files={len(test_result.generated_files)}")

        reference_result = generate_reference_code(
            task_id=task_id,
            language=language,
            original_requirement_text=original_requirement_text,
            api_config=api_config,
            code_output_dir=str(case_output_dir / "reference"),
            prompt_text=reference_code_prompt_text,
        )
        print(f"[generate_case] task={task_id} reference done implementations={len(reference_result.implementations)}")

        print(f"[generate_case] task={task_id} complete output={case_output_dir}")

    print("[generate_case] all cases complete")


if __name__ == "__main__":
    run_generate_case()

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from generate_case.case_metrics.case_io import load_json, save_case_metrics_result
from generate_case.case_metrics.service import evaluate_case_metrics
from generate_case.test_generation.case_io import list_case_paths
from shared.case_text import load_case


def run_case_metrics(task_id: str | None = None) -> None:
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
    metric_config = dict(stage_config.get("metric_config", {}))

    total_cases = len(case_paths)
    print(f"[case_metrics] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        task_id = case_path.stem
        print(f"[case_metrics] case {case_index}/{total_cases} task={task_id}")

        case_data = load_case(case_path)
        original_requirement_text = case_data["body"]

        case_output_dir = Path(output_cases_dir) / task_id
        case_output_dir.mkdir(parents=True, exist_ok=True)

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
        print(f"[case_metrics] task={task_id} done")

    print("[case_metrics] all cases complete")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run case metrics evaluation")
    parser.add_argument("--task-id", help="Process a single case by task ID")
    args = parser.parse_args()
    run_case_metrics(task_id=args.task_id)

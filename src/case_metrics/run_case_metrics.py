import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_metrics.case_io import build_result_path, list_result_paths, load_json, save_case_metrics_result
from case_metrics.service import evaluate_case_metrics


def run_case_metrics() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stage_config = load_json(str(project_root / "config" / "case_metrics.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))

    source_result_paths = list_result_paths(
        str(project_root / stage_config["case_spec_generation_results_dir"]),
        str(stage_config["case_spec_generation_result_glob"]),
    )
    results_dir = str(project_root / stage_config["results_dir"])
    metric_config = dict(stage_config.get("metric_config", {}))
    total_cases = len(source_result_paths)
    print(f"[case_metrics] start total_cases={total_cases}")

    for case_index, source_result_path in enumerate(source_result_paths, start=1):
        print(f"[case_metrics] case {case_index}/{total_cases} source={source_result_path}")
        expansion_result = load_json(str(source_result_path))
        expansion_result.setdefault("summary", {})
        expansion_result["summary"]["result_path"] = str(source_result_path)
        result = evaluate_case_metrics(expansion_result, api_config, metric_config)
        save_case_metrics_result(str(build_result_path(results_dir, result.task_id)), result)
        print(f"[case_metrics] done task={result.task_id} result={build_result_path(results_dir, result.task_id)}")
    print("[case_metrics] complete")


if __name__ == "__main__":
    run_case_metrics()

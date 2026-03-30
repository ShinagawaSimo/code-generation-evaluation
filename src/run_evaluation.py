from pathlib import Path

from data_process.data_io import load_config, load_prompt
from eval_core import EvaluationPipeline, EvaluationRunner
from eval_core.registry import resolve_steps


def run() -> None:
    """
    Load configuration, construct pipeline, and run evaluation for all cases.
    """
    pipeline_config = load_config("config/eval_pipeline.json")
    steps = resolve_steps(pipeline_config["steps"])
    pipeline = EvaluationPipeline(steps=steps)
    runner = EvaluationRunner(pipeline=pipeline)
    prompt = load_prompt(pipeline_config["prompt_path"])
    model_api_config = load_config("config/model_api.json")
    run_config = load_config("config/run_cases.json")
    cases_dir = Path(run_config.get("cases_dir", "src/cases/independent_generation"))
    case_glob = run_config.get("case_glob", "independent_case_*.json")
    results_dir = Path(run_config.get("results_dir", "src/results/independent_generation"))
    raw_output_dir = Path(run_config.get("raw_output_dir", "artifacts/raw_outputs"))
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_output_dir.mkdir(parents=True, exist_ok=True)
    case_paths = sorted(cases_dir.glob(case_glob))
    for case_path in case_paths:
        case_name = case_path.stem
        output_path = results_dir / f"{case_name}_result.json"
        raw_output_path = raw_output_dir / f"{case_name}.txt"
        runner.run_from_json(
            str(case_path),
            str(output_path),
            extra_metrics_inputs={
                "model_prompt": prompt,
                "model_api_config": model_api_config,
                "raw_output_path": str(raw_output_path),
            },
        )


if __name__ == "__main__":
    run()

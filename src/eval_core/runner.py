from pathlib import Path
from typing import Any, Dict

from data_process.data_io import load_json, save_json
from .models import EvaluationContext
from .pipeline import EvaluationPipeline


def _compact_run_records(run_records: Dict[str, Any]) -> Dict[str, Any]:
    compact: Dict[str, Any] = {}
    model_error = run_records.get("model_error")
    if model_error:
        compact["model_error"] = model_error
    build = run_records.get("build")
    if isinstance(build, dict):
        compact["build"] = {
            "success": bool(build.get("success")),
            "error": build.get("error", ""),
            "workspace": build.get("workspace", ""),
            "language": build.get("language", ""),
            "source_path": build.get("source_path", ""),
            "output_path": build.get("output_path", ""),
            "build_command": build.get("build_command", []),
            "run_command": build.get("run_command", []),
            "returncode": build.get("returncode"),
        }
    sample_tests = run_records.get("sample_tests")
    if isinstance(sample_tests, dict):
        compact_cases = []
        for case in sample_tests.get("cases", []):
            if not isinstance(case, dict):
                continue
            compact_cases.append(
                {
                    "input": case.get("input", ""),
                    "expected_output": case.get("expected_output", ""),
                    "actual_output": case.get("actual_output", ""),
                    "returncode": case.get("returncode"),
                    "passed": bool(case.get("passed")),
                }
            )
        compact["sample_tests"] = {
            "passed": bool(sample_tests.get("passed")),
            "cases": compact_cases,
        }
    raw_output_path = run_records.get("raw_output_path")
    if raw_output_path:
        compact["raw_output_path"] = raw_output_path
    return compact


def _build_result_record(context: EvaluationContext, run_records: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "instance_id": context.instance_id,
        "task_type": context.task_type,
        "language": context.language,
        "case_path": context.metrics_inputs.get("case_path", ""),
        "run_records": _compact_run_records(run_records),
        "evaluation_result": context.evaluation_result,
    }


class EvaluationRunner:
    def __init__(self, pipeline: EvaluationPipeline | None = None) -> None:
        """
        Initialize a runner with a pipeline instance.
        pipeline: evaluation pipeline to execute.
        """
        self.pipeline = pipeline or EvaluationPipeline()

    def run(self, context: EvaluationContext) -> EvaluationContext:
        """
        Run the pipeline over a prepared evaluation context.
        context: evaluation context to execute.
        """
        return self.pipeline.run(context)

    def run_from_json(
        self,
        input_path: str,
        output_path: str,
        default_metrics_inputs: Dict[str, Any] | None = None,
        default_metrics_config: Dict[str, Any] | None = None,
        extra_metrics_inputs: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Load context from JSON, run pipeline, and persist results.
        input_path: JSON path with evaluation context fields.
        output_path: JSON path to write evaluation results.
        extra_metrics_inputs: optional runtime metrics inputs.
        """
        data = load_json(input_path)
        metrics_inputs = data.get("metrics_inputs") or {}
        if default_metrics_inputs:
            for key, value in default_metrics_inputs.items():
                metrics_inputs.setdefault(key, value)
        data["metrics_inputs"] = metrics_inputs
        metrics_config = data.get("metrics_config") or {}
        if default_metrics_config:
            for key, value in default_metrics_config.items():
                metrics_config.setdefault(key, value)
        data["metrics_config"] = metrics_config
        context = EvaluationContext(**data)
        if extra_metrics_inputs:
            context.metrics_inputs.update(extra_metrics_inputs)
        result = self.run(context)
        run_records = dict(result.run_records or {})
        raw_output = run_records.get("raw_output", "")
        raw_output_path = context.metrics_inputs.get("raw_output_path") or run_records.get("raw_output_path")
        if raw_output_path:
            Path(raw_output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(raw_output_path).write_text(str(raw_output), encoding="utf-8")
            run_records.pop("raw_output", None)
            run_records["raw_output_path"] = raw_output_path
        record = _build_result_record(result, run_records)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        save_json(output_path, record)
        return record

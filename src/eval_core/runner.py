from pathlib import Path
from typing import Any, Dict

from data_process.data_io import load_json, save_json
from .models import EvaluationContext
from .pipeline import EvaluationPipeline


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
        extra_metrics_inputs: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Load context from JSON, run pipeline, and persist results.
        input_path: JSON path with evaluation context fields.
        output_path: JSON path to write evaluation results.
        extra_metrics_inputs: optional runtime metrics inputs.
        """
        data = load_json(input_path)
        context = EvaluationContext(**data)
        if extra_metrics_inputs:
            context.metrics_inputs.update(extra_metrics_inputs)
        result = self.run(context)
        record = result.to_record()
        record["evaluation_result"] = result.evaluation_result
        run_records = dict(record.get("run_records", {}))
        raw_output = run_records.get("raw_output", "")
        raw_output_path = context.metrics_inputs.get("raw_output_path") or run_records.get("raw_output_path")
        if raw_output_path:
            Path(raw_output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(raw_output_path).write_text(str(raw_output), encoding="utf-8")
            run_records.pop("raw_output", None)
            run_records["raw_output_path"] = raw_output_path
        record["run_records"] = run_records
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        save_json(output_path, record)
        return record

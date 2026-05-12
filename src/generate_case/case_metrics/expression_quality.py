import json
from pathlib import Path
from typing import Any, Dict

from shared.model_client import call_model

from .models import MetricResult


DEFAULT_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "expression_quality_prompt.txt"
)


def _extract_json_block(raw_output: str) -> str:
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model output does not contain a JSON object")
    return stripped[start : end + 1]


def _load_prompt(prompt_path: str | None = None) -> str:
    target = Path(prompt_path) if prompt_path else DEFAULT_PROMPT_PATH
    return target.read_text(encoding="utf-8")


def _build_llm_input(original_requirement_text: str) -> str:
    return json.dumps(
        {
            "original_requirement_text": original_requirement_text,
            "task": "Check term consistency and understandability issues in original requirement text.",
        },
        ensure_ascii=False,
        indent=2,
    )


def evaluate_expression_quality(
    original_requirement_text: str,
    api_config: Dict[str, Any],
    metric_config: Dict[str, Any],
) -> MetricResult:
    raw_output, *_ = call_model(
        api_config,
        _load_prompt(metric_config.get("expression_quality_prompt_path")),
        _build_llm_input(original_requirement_text),
    )
    parsed = json.loads(_extract_json_block(raw_output))
    consistency_issues = list(parsed.get("consistency_issues", []))
    understandability_issues = list(parsed.get("understandability_issues", []))
    return MetricResult(
        values={
            "consistency": {
                "issue_count": len(consistency_issues),
                "issues": consistency_issues,
            },
            "understandability": {
                "issue_count": len(understandability_issues),
                "issues": understandability_issues,
            },
        },
    )

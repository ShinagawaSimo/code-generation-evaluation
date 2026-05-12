import json
from pathlib import Path
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import MetricResult
from .tokenizer import count_tokens


DEFAULT_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "private_knowledge_dependency_prompt.txt"
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


def _build_input(original_requirement_text: str) -> str:
    return json.dumps(
        {
            "original_requirement_text": original_requirement_text,
            "task": "Identify private or domain-specific knowledge spans in original requirement text.",
        },
        ensure_ascii=False,
        indent=2,
    )


def _unique_spans(spans: List[str]) -> List[str]:
    unique: List[str] = []
    seen = set()
    for span in spans:
        cleaned = span.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


def evaluate_private_knowledge_dependency(
    original_requirement_text: str,
    api_config: Dict[str, Any],
    metric_config: Dict[str, Any],
) -> MetricResult:
    raw_output, *_ = call_model(
        api_config,
        _load_prompt(metric_config.get("private_knowledge_dependency_prompt_path")),
        _build_input(original_requirement_text),
    )
    parsed = json.loads(_extract_json_block(raw_output))
    spans = _unique_spans([str(span) for span in parsed.get("private_knowledge_spans", [])])
    private_knowledge_token_count = sum(count_tokens(span, metric_config) for span in spans)
    total_token_count = count_tokens(original_requirement_text, metric_config)
    dependency_ratio = (
        private_knowledge_token_count / total_token_count if total_token_count else 0.0
    )
    return MetricResult(
        values={
            "private_knowledge_spans": spans,
            "private_knowledge_token_count": private_knowledge_token_count,
            "total_token_count": total_token_count,
            "dependency_ratio": dependency_ratio,
        },
    )

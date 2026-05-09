import json
import re
from pathlib import Path
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import MetricResult


DEFAULT_PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "expression_quality_prompt.txt"
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


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？!?;；])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _build_sentence_point_map(expansion_result: Dict[str, Any]) -> Dict[str, List[str]]:
    sentence_map: Dict[str, List[str]] = {}
    for point in expansion_result["requirement_points"]:
        if not point["is_explicit_in_original"]:
            continue
        point_id = str(point["point_id"])
        for fragment in point["original_source_texts"]:
            for sentence in _split_sentences(str(fragment)):
                sentence_map.setdefault(sentence, []).append(point_id)
    return sentence_map


def _evaluate_atomicity(expansion_result: Dict[str, Any]) -> Dict[str, Any]:
    explicit_points = [
        point for point in expansion_result["requirement_points"] if point["is_explicit_in_original"]
    ]
    sentence_map = _build_sentence_point_map(expansion_result)
    standalone_point_ids = sorted(
        {
            point_ids[0]
            for point_ids in sentence_map.values()
            if len(set(point_ids)) == 1
        }
    )
    mixed_sentences = [
        {"sentence": sentence, "point_ids": point_ids}
        for sentence, point_ids in sentence_map.items()
        if len(set(point_ids)) > 1
    ]
    explicit_requirement_point_count = len(explicit_points)
    standalone_sentence_point_count = len(set(standalone_point_ids))
    atomicity_ratio = (
        standalone_sentence_point_count / explicit_requirement_point_count
        if explicit_requirement_point_count
        else 0.0
    )
    return {
        "explicit_requirement_point_count": explicit_requirement_point_count,
        "standalone_sentence_point_count": standalone_sentence_point_count,
        "atomicity_ratio": atomicity_ratio,
        "standalone_point_ids": standalone_point_ids,
        "mixed_sentences": mixed_sentences,
    }


def _build_llm_input(original_requirement_text: str, expansion_result: Dict[str, Any]) -> str:
    explicit_points = [
        {
            "point_id": point["point_id"],
            "point_text": point["point_text"],
            "category": point["category"],
            "original_source_texts": point["original_source_texts"],
        }
        for point in expansion_result["requirement_points"]
        if point["is_explicit_in_original"]
    ]
    return json.dumps(
        {
            "original_requirement_text": original_requirement_text,
            "explicit_requirement_points": explicit_points,
            "task": "Check term consistency and understandability issues in original requirement text.",
        },
        ensure_ascii=False,
        indent=2,
    )


def evaluate_expression_quality(
    original_requirement_text: str,
    expansion_result: Dict[str, Any],
    api_config: Dict[str, Any],
    metric_config: Dict[str, Any],
) -> MetricResult:
    atomicity = _evaluate_atomicity(expansion_result)
    raw_output, *_ = call_model(
        api_config,
        _load_prompt(metric_config.get("expression_quality_prompt_path")),
        _build_llm_input(original_requirement_text, expansion_result),
    )
    parsed = json.loads(_extract_json_block(raw_output))
    consistency_issues = list(parsed.get("consistency_issues", []))
    understandability_issues = list(parsed.get("understandability_issues", []))
    return MetricResult(
        values={
            "atomicity": atomicity,
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

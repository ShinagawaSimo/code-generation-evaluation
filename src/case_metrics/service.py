from typing import Any, Dict

from .case_scale import evaluate_case_scale
from .expression_format import evaluate_expression_format
from .expression_quality import evaluate_expression_quality
from .models import CaseMetricsResult
from .private_knowledge_dependency import evaluate_private_knowledge_dependency
from .specification_completeness import evaluate_specification_completeness
from .specification_complexity import evaluate_specification_complexity


def evaluate_case_metrics(
    expansion_result: Dict[str, Any],
    api_config: Dict[str, Any],
    metric_config: Dict[str, Any],
) -> CaseMetricsResult:
    original_requirement_text = str(expansion_result.get("original_requirement_text", ""))
    metrics = {
        "specification_complexity": evaluate_specification_complexity(expansion_result),
        "specification_completeness": evaluate_specification_completeness(expansion_result),
        "private_knowledge_dependency": evaluate_private_knowledge_dependency(
            original_requirement_text, api_config, metric_config
        ),
        "case_scale": evaluate_case_scale(original_requirement_text, metric_config),
        "expression_format": evaluate_expression_format(expansion_result),
        "expression_quality": evaluate_expression_quality(
            original_requirement_text, expansion_result, api_config, metric_config
        ),
    }
    return CaseMetricsResult(
        task_id=str(expansion_result.get("task_id", "")),
        original_requirement_text=original_requirement_text,
        metrics=metrics,
        summary={
            "requirement_expansion_result_path": expansion_result.get("summary", {}).get("result_path", ""),
        },
    )

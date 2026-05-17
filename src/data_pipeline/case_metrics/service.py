from typing import Any, Dict

from .case_scale import evaluate_case_scale
from .expression_format import evaluate_expression_format
from .expression_quality import evaluate_expression_quality
from .models import CaseMetricsResult
from .private_knowledge_dependency import evaluate_private_knowledge_dependency
from .specification_completeness import evaluate_specification_completeness
from .specification_complexity import evaluate_specification_complexity


def evaluate_case_metrics(
    task_id: str,
    original_requirement_text: str,
    api_config: Dict[str, Any],
    metric_config: Dict[str, Any],
) -> CaseMetricsResult:
    cases_dir = str(metric_config.get("cases_dir", "cases"))

    spec_complexity = evaluate_specification_complexity(task_id, cases_dir)
    spec_completeness = evaluate_specification_completeness()
    priv_knowledge = evaluate_private_knowledge_dependency(
        original_requirement_text, api_config, metric_config
    )
    scale = evaluate_case_scale(original_requirement_text, metric_config)
    expr_format = evaluate_expression_format(original_requirement_text)
    expr_quality = evaluate_expression_quality(
        original_requirement_text, api_config, metric_config
    )

    metrics = {
        "specification_complexity": spec_complexity,
        "specification_completeness": spec_completeness,
        "private_knowledge_dependency": priv_knowledge,
        "case_scale": scale,
        "expression_format": expr_format,
        "expression_quality": expr_quality,
    }

    cv = spec_complexity.values
    cv2 = spec_completeness.values
    pv = priv_knowledge.values
    sv = scale.values
    ev = expr_format.values
    eqv = expr_quality.values
    summary = {
        "specification_complexity": cv["complexity_rating"],
        "specification_completeness": cv2["completeness_ratio"],
        "private_knowledge_dependency": pv["private_knowledge_token_count"],
        "case_scale": {
            "token_count": sv["token_count"],
            "requirement_point_count": sv["requirement_point_count"],
        },
        "expression_format": ev["ears_ratio"],
        "expression_quality": {
            "consistency": eqv["consistency"]["issue_count"],
            "understandability": eqv["understandability"]["issue_count"],
        },
    }

    return CaseMetricsResult(
        task_id=task_id,
        original_requirement_text=original_requirement_text,
        metrics=metrics,
        summary=summary,
    )

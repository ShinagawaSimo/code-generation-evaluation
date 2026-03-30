from typing import Tuple

from .models import EvaluationContext


def evaluate_build(context: EvaluationContext) -> Tuple[float, bool]:
    """
    Compute build score and success flag from metrics inputs.
    context: evaluation context providing build_success and weights.
    """
    build_success = bool(context.metrics_inputs.get("build_success", True))
    weight = context.metrics_config.get("build_weight", 1.0)
    return (weight if build_success else -weight), build_success


def evaluate_process_metrics(context: EvaluationContext) -> float:
    """
    Score process metrics based on explicit flag or thresholds.
    context: evaluation context with metrics inputs and thresholds.
    """
    explicit_ok = context.metrics_inputs.get("process_metrics_ok")
    if explicit_ok is not None:
        within_bounds = bool(explicit_ok)
    else:
        response_time_ms = context.metrics_inputs.get("response_time_ms")
        token_usage = context.metrics_inputs.get("token_usage")
        cost_usd = context.metrics_inputs.get("cost_usd")
        max_response_time_ms = context.metrics_config.get("max_response_time_ms")
        max_token_usage = context.metrics_config.get("max_token_usage")
        max_cost_usd = context.metrics_config.get("max_cost_usd")
        checks = []
        if max_response_time_ms is not None and response_time_ms is not None:
            checks.append(float(response_time_ms) <= float(max_response_time_ms))
        if max_token_usage is not None and token_usage is not None:
            checks.append(int(token_usage) <= int(max_token_usage))
        if max_cost_usd is not None and cost_usd is not None:
            checks.append(float(cost_usd) <= float(max_cost_usd))
        within_bounds = all(checks) if checks else True
    weight = context.metrics_config.get("process_weight", 1.0)
    return weight if within_bounds else -weight


def evaluate_sample_tests(context: EvaluationContext) -> Tuple[float, bool]:
    """
    Score sample test results and return pass flag.
    context: evaluation context with sample_tests_pass and weight.
    """
    passed = bool(context.metrics_inputs.get("sample_tests_pass", False))
    weight = context.metrics_config.get("sample_tests_weight", 1.0)
    return (weight if passed else -weight), passed


def compute_final_score(context: EvaluationContext) -> float:
    """
    Aggregate all accumulated scores into a final value.
    context: evaluation context containing score deltas.
    """
    return sum(context.scores.values())

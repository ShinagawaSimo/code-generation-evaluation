from .models import MetricResult


def evaluate_specification_completeness() -> MetricResult:
    return MetricResult(
        values={
            "completeness_ratio": 1.0,
        },
    )

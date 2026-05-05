from typing import Any, Dict

from .models import MetricResult
from .tokenizer import count_tokens


def evaluate_case_scale(original_requirement_text: str, metric_config: Dict[str, Any]) -> MetricResult:
    token_count = count_tokens(original_requirement_text, metric_config)
    return MetricResult(
        name="case_scale",
        values={
            "token_count": token_count,
            "tokenizer_backend": str(metric_config.get("tokenizer_backend", "tiktoken")),
            "tokenizer_model": str(metric_config.get("tokenizer_model", "")),
            "tokenizer_encoding": str(metric_config.get("tokenizer_encoding", "")),
        },
    )

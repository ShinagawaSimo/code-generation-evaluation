import re
from typing import List

from .models import MetricResult


EARS_PATTERNS = [
    re.compile(r"^\s*(当|如果|在.+状态下|若|一旦).+"),
    re.compile(r"^\s*(When|If|While|Where|Once).+", re.IGNORECASE),
    re.compile(r".+\s*(应|必须|shall|should)\s*.+", re.IGNORECASE),
]


def _matches_ears(text: str) -> bool:
    return any(pattern.search(text) for pattern in EARS_PATTERNS)


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？!?;；])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def evaluate_expression_format(original_requirement_text: str) -> MetricResult:
    sentences = _split_sentences(original_requirement_text)
    matched_count = sum(1 for sentence in sentences if _matches_ears(sentence))
    total_count = len(sentences)
    ears_ratio = matched_count / total_count if total_count else 0.0
    return MetricResult(
        values={
            "total_sentence_count": total_count,
            "ears_match_count": matched_count,
            "ears_ratio": ears_ratio,
        },
    )

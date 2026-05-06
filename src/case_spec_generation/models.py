from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal


RequirementPointCategory = Literal[
    "basic_function",
    "implicit_function",
    "optional_function",
    "basic_non_function",
    "optional_non_function",
]


def _default_classification_labels() -> List[str]:
    return [
        "basic_function",
        "implicit_function",
        "optional_function",
        "basic_non_function",
        "optional_non_function",
    ]


@dataclass
class CaseSpecRequest:
    task_id: str
    original_requirement_text: str
    language: str = ""
    extra_context: Dict[str, Any] = field(default_factory=dict)
    allow_optional_features: bool = True
    preserve_user_constraints: bool = True
    output_language: str = "zh-CN"
    classification_labels: List[str] = field(default_factory=_default_classification_labels)

    def to_prompt_payload(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "original_requirement_text": self.original_requirement_text,
            "extra_context": self.extra_context,
            "allow_optional_features": self.allow_optional_features,
            "preserve_user_constraints": self.preserve_user_constraints,
            "output_language": self.output_language,
            "classification_labels": list(self.classification_labels),
        }


@dataclass
class RequirementPoint:
    point_id: str
    point_text: str
    category: RequirementPointCategory
    is_explicit_in_original: bool
    original_source_texts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "point_text": self.point_text,
            "category": self.category,
            "is_explicit_in_original": self.is_explicit_in_original,
            "original_source_texts": list(self.original_source_texts),
        }


@dataclass
class CaseSpecResult:
    task_id: str
    language: str
    original_requirement_text: str
    requirement_points: List[RequirementPoint] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "original_requirement_text": self.original_requirement_text,
            "requirement_points": [point.to_dict() for point in self.requirement_points],
            "summary": self.summary,
        }

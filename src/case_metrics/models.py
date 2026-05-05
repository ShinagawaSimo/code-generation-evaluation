from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MetricResult:
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = {"name": self.name, "values": self.values}
        if self.raw_response:
            data["raw_response"] = self.raw_response
        return data


@dataclass
class CaseMetricsResult:
    task_id: str
    original_requirement_text: str
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "original_requirement_text": self.original_requirement_text,
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "summary": self.summary,
        }

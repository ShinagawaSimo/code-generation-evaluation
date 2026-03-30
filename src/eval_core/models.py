from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvaluationContext:
    instance_id: str
    repo: str
    version: str
    task_type: str
    language: str
    task_original_statement: str
    is_original_task: bool
    task_revision_statement: str
    input_direct: Dict[str, Any]
    input_indirect: Dict[str, Any]
    expected_output: Dict[str, Any]
    tangling_level_input: int
    scattering_level_input: int
    scale_level_input: int
    domain_knowledge_dependence_input: int
    number_of_multimodal_input: int
    tangling_level_output: int
    scattering_level_output: int
    scale_level_output: int
    number_of_multimodal_output: int
    comprehensive_difficulty_level: int
    base_commit: str
    patch: str
    test_setup_id: str
    hints_text: str
    model_input: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metrics_config: Dict[str, Any] = field(default_factory=dict)
    metrics_inputs: Dict[str, Any] = field(default_factory=dict)
    run_records: Dict[str, Any] = field(default_factory=dict)
    evaluation_result: Dict[str, Any] = field(default_factory=dict)
    scores: Dict[str, float] = field(default_factory=dict)
    flags: Dict[str, Any] = field(default_factory=dict)

    def apply_score(self, key: str, delta: float) -> None:
        """
        Apply a score delta to a named score bucket.
        key: score bucket name.
        delta: score delta to add.
        """
        self.scores[key] = self.scores.get(key, 0.0) + float(delta)

    def set_flag(self, key: str, value: Any) -> None:
        """
        Set a boolean or metadata flag on the context.
        key: flag name.
        value: flag value to store.
        """
        self.flags[key] = value

    def to_record(self) -> Dict[str, Any]:
        """
        Serialize the evaluation context into a dictionary record.
        """
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "version": self.version,
            "task_type": self.task_type,
            "language": self.language,
            "task_original_statement": self.task_original_statement,
            "is_original_task": self.is_original_task,
            "task_revision_statement": self.task_revision_statement,
            "input_direct": self.input_direct,
            "input_indirect": self.input_indirect,
            "expected_output": self.expected_output,
            "tangling_level_input": self.tangling_level_input,
            "scattering_level_input": self.scattering_level_input,
            "scale_level_input": self.scale_level_input,
            "domain_knowledge_dependence_input": self.domain_knowledge_dependence_input,
            "number_of_multimodal_input": self.number_of_multimodal_input,
            "tangling_level_output": self.tangling_level_output,
            "scattering_level_output": self.scattering_level_output,
            "scale_level_output": self.scale_level_output,
            "number_of_multimodal_output": self.number_of_multimodal_output,
            "comprehensive_difficulty_level": self.comprehensive_difficulty_level,
            "base_commit": self.base_commit,
            "patch": self.patch,
            "test_setup_id": self.test_setup_id,
            "hints_text": self.hints_text,
            "model_input": self.model_input,
            "tags": self.tags,
            "metrics_config": self.metrics_config,
            "run_records": self.run_records,
            "evaluation_result": self.evaluation_result,
        }

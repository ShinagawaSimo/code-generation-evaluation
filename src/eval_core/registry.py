from typing import Callable, Dict, List

from .models import EvaluationContext
from .steps_input import (
    capture_artifacts,
    context_validation,
    generate_output,
    input_assembly,
    task_intake_scope_lock,
)
from .steps_scoring import (
    compile_build_check,
    difficulty_confirmation,
    final_score,
    process_metrics_check,
    sample_tests_check,
)


STEP_REGISTRY: Dict[str, Callable[[EvaluationContext], EvaluationContext]] = {
    "task_intake_scope_lock": task_intake_scope_lock,
    "input_assembly": input_assembly,
    "context_validation": context_validation,
    "generate_output": generate_output,
    "capture_artifacts": capture_artifacts,
    "compile_build_check": compile_build_check,
    "process_metrics_check": process_metrics_check,
    "sample_tests_check": sample_tests_check,
    "difficulty_confirmation": difficulty_confirmation,
    "final_score": final_score,
}


def resolve_steps(step_names: List[str]) -> List[Callable[[EvaluationContext], EvaluationContext]]:
    """
    Resolve step names into callable functions.
    step_names: ordered list of step identifiers from config.
    """
    return [STEP_REGISTRY[name] for name in step_names]

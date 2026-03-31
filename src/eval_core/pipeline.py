from typing import Callable, Sequence

from .models import EvaluationContext
from .steps_input import generate_output
from .steps_scoring import (
    compile_build_check,
    difficulty_confirmation,
    final_score,
    process_metrics_check,
    sample_tests_check,
)


class EvaluationPipeline:
    default_steps: Sequence[Callable[[EvaluationContext], EvaluationContext]] = (
        generate_output,
        compile_build_check,
        sample_tests_check,
        process_metrics_check,
        difficulty_confirmation,
        final_score,
    )

    def __init__(
        self, steps: Sequence[Callable[[EvaluationContext], EvaluationContext]] | None = None
    ) -> None:
        """
        Build a pipeline with a sequence of evaluation steps.
        steps: ordered callables that transform EvaluationContext.
        """
        self.steps = list(steps or self.default_steps)

    def run(self, context: EvaluationContext) -> EvaluationContext:
        """
        Execute each step in order and return the final context.
        context: evaluation context to be processed.
        """
        for step in self.steps:
            print(f"[pipeline] running: {step.__name__}")
            context = step(context)
        print("[pipeline] completed")
        return context

from data_process.build_tools import build_executable
from data_process.execution import run_sample_tests
from .metrics import (
    compute_final_score,
    evaluate_build,
    evaluate_process_metrics,
    evaluate_sample_tests,
)
from .models import EvaluationContext


def compile_build_check(context: EvaluationContext) -> EvaluationContext:
    """
    Compile the generated code and record build artifacts and result.
    context: evaluation context carrying model output and build configuration.
    """
    raw_output = context.run_records.get("raw_output", "")
    build_workspace = context.metrics_inputs.get("build_workspace", "artifacts/independent_build")
    source_name = context.metrics_inputs.get("build_source_name")
    output_name = context.metrics_inputs.get("build_output_name")
    case_id = context.metrics_inputs.get("case_id") or context.instance_id
    build_result = build_executable(
        language=context.language,
        raw_output=raw_output,
        workspace=build_workspace,
        source_name=source_name,
        output_name=output_name,
        case_id=case_id,
    )
    context.run_records["build"] = build_result
    build_success = bool(build_result.get("success"))
    context.metrics_inputs["build_success"] = build_success
    score_delta, _ = evaluate_build(context)
    context.apply_score("build", score_delta)
    context.set_flag("build_success", build_success)
    return context


def sample_tests_check(context: EvaluationContext) -> EvaluationContext:
    """
    Run sample input/output tests using the compiled executable or script.
    context: evaluation context containing build result and reference samples.
    """
    if not context.flags.get("build_success", True):
        context.set_flag("sample_tests_pass", False)
        return context
    build_record = context.run_records.get("build", {})
    run_command = build_record.get("run_command") or []
    samples = context.model_input.get("reference_samples") or []
    timeout_seconds = int(context.metrics_inputs.get("sample_test_timeout_seconds", 10))
    if run_command and samples:
        result = run_sample_tests(run_command, samples, build_record.get("workspace", ""), timeout_seconds)
        passed = bool(result.get("passed"))
        context.run_records["sample_tests"] = result
        context.metrics_inputs["sample_tests_pass"] = passed
    else:
        passed = True
        context.metrics_inputs["sample_tests_pass"] = passed
    score_delta, passed = evaluate_sample_tests(context)
    context.apply_score("sample_tests", score_delta)
    context.set_flag("sample_tests_pass", passed)
    return context


def process_metrics_check(context: EvaluationContext) -> EvaluationContext:
    """
    Score process metrics such as latency, token usage, and cost thresholds.
    context: evaluation context with metrics inputs and thresholds.
    """
    score_delta = evaluate_process_metrics(context)
    context.apply_score("process", score_delta)
    return context


def difficulty_confirmation(context: EvaluationContext) -> EvaluationContext:
    """
    Apply difficulty override if provided by evaluators.
    context: evaluation context with optional difficulty override.
    """
    override = context.metrics_inputs.get("difficulty_override")
    if override is not None:
        context.comprehensive_difficulty_level = int(override)
    return context


def final_score(context: EvaluationContext) -> EvaluationContext:
    """
    Aggregate scores and finalize pass/fail decision.
    context: evaluation context with accumulated scores and flags.
    """
    context.evaluation_result["scores"] = dict(context.scores)
    context.evaluation_result["final_score"] = compute_final_score(context)
    build_success = context.flags.get("build_success", True)
    sample_tests_pass = context.flags.get("sample_tests_pass", True)
    context.evaluation_result["passed"] = (
        context.evaluation_result["final_score"] >= 0.0 and build_success and sample_tests_pass
    )
    context.evaluation_result["review_notes"] = context.metrics_inputs.get("review_notes", "")
    return context

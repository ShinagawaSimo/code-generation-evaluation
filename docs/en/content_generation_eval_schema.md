 # Content Generation Evaluation Sample Schema
 
 ## Field Definitions
 - instance_id: unique identifier for the evaluation sample.
 - repo: source repository name for context.
 - version: repository version when the task is defined.
 - task_type: independent_function_development | new_application_development | incremental_feature_development.
 - language: primary programming language for the task.
 - task_original_statement: original task description used as primary input.
 - is_original_task: whether the task statement is original.
 - task_revision_statement: revised task statement when difficulty or scope is adjusted.
 - input_direct: direct inputs provided to the model, including code and instructions.
 - input_indirect: indirect inputs such as repo context and external knowledge.
 - expected_output: expected artifacts and acceptance criteria for correct completion.
 - difficulty_spec: case-level overrides (subtask_count, algorithm_complexity_level, ambiguity_score).
 - base_commit: base commit hash for the task.
 - patch: expected code changes in diff format when applicable.
 - test_setup_id: environment setup identifier for execution.
 - hints_text: optional hints for additional context.
 - tags: optional tags for batch selection.
 - metrics_config: metric definitions and weights for scoring (difficulty_metric_weights, quality_metric_weights, difficulty_score_caps, quality_score_caps, difficulty_weight).
 - metrics_inputs: runtime parameters and inputs (e.g., sample timeout, tool turns, build workspace, raw_output_path, plus optional overrides such as subtask_count, algorithm_complexity_level, ambiguity_score, semantic_consistency_score, style_score, performance_score, robustness_score).
 - run_records: execution logs, outputs, and intermediate artifacts.
 - evaluation_result: computed scores, pass/fail flags, review notes, and automated summaries (metrics, difficulty, quality, quality_score_q, difficulty_score_d, final_score).

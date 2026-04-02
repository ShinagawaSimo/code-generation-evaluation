 # Content Generation Evaluation Sample Schema
 
 ## Field Definitions
 - instance_id: unique identifier for the evaluation sample.
 - task_type: independent_function_development | new_application_development | incremental_feature_development.
 - language: primary programming language for the task.
 - task_original_statement: original task description used as primary input.
 - input_direct: direct inputs provided to the model, including code and instructions.
 - input_indirect: indirect inputs such as repo context and external knowledge.
 - expected_output: expected artifacts and acceptance criteria for correct completion.
 - difficulty_spec: case-level overrides (subtask_count, algorithm_complexity_level, ambiguity_score).
- model_input: primary model input payload (task description, samples, code skeleton).
- metrics_inputs: runtime inputs (e.g., case_id, case_path, and optional overrides such as subtask_count, algorithm_complexity_level, ambiguity_score).

## Persisted Result Fields (Compacted)
- instance_id: sample identifier.
- task_type: task category.
- language: language label.
- case_path: source case path for traceability.
- run_records: only deterministic evaluation records are persisted:
  - build: success, error, workspace, language, source_path, output_path, build_command, run_command, returncode.
  - sample_tests: passed plus per-case input, expected_output, actual_output, returncode, passed.
  - raw_output_path: file path of raw model output.
  - model_error: error message when model call/output is invalid (if present).
- evaluation_result: full scoring payload including metrics, difficulty, quality, quality_score_q, difficulty_score_d, scores, final_score, passed, review_notes.

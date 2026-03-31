 # Code Generation Evaluation Project Document
 
## Project Structure
- config: evaluation configuration and runtime parameters (eval_pipeline.json, run_cases.json, model_api.json).
- src/cases: evaluation case inputs.
- src/eval_core: evaluation pipeline and metric computation.
- src/data_process: build, execution, and data IO utilities.
- docs: project documentation and evaluation specs.
- artifacts/raw_outputs: archived raw model outputs.
- artifacts/results: archived evaluation results.

 ## Content Generation Evaluation Specification
 
 ### Task Inputs and Outputs
 - Input, direct: prompts, provided code/text, and explicit instructions given to the model.
 - Input, indirect: repository context and external knowledge required to solve the task.
 - Output, expected: code, text, code changes, and required explanations for correct completion.
 - Output, actual: generated artifacts captured for evaluation and traceability.
 
 ### Evaluation Principles
 - Alignment with expected output: test pass, text match, location match, semantic match (hit@k, recall@k).
 - Necessity allowance: outputs that differ but are correct, necessary, and valuable.
 - Code quality: style, safety, performance, and maintainability considerations.
 - Process evidence: intermediate results and decision traces when available.
 
 ### Difficulty System
 - tangling/scattering/scale/domain/modality fields are no longer used.
 - D comes from the Code Difficulty module only.
 - Code Difficulty module:
   - Input scale complexity: task text length, reference code length, reference function count.
   - Output complexity: output field count, output function count, return nesting depth, complex object involvement.
   - Subtask count: auto-estimated, override via difficulty_spec or metrics_inputs.
   - Algorithm complexity level: auto-estimated, override via difficulty_spec or metrics_inputs.
   - Constraint complexity: constraint keyword count.
   - Ambiguity: default 0, override via ambiguity_score.
   - Test difficulty: sample count, boundary ratio, input-space size.
 - D is the weighted average of normalized difficulty indicators using difficulty_metric_weights.

 ### Quality System
 - Code Quality module:
   - Correctness: build_success and sample_tests_pass.
   - Semantic consistency: semantic_consistency_score.
   - Structural quality: function count, average function length, max nesting depth.
   - Readability: identifier statistics and comment density.
   - Style compliance: style_score.
   - Performance: performance_score or complexity-hint fallback.
   - Robustness and security: robustness_score.
 - Q is the weighted average of normalized quality indicators using quality_metric_weights.
 - Final score: Score = Q ⋅ (1 + λD), where λ is difficulty_weight.

## Configuration Notes
- config/run_cases.json: case paths, result directory, raw output directory, plus default metrics_inputs/metrics_config.
- config/eval_pipeline.json: ordered evaluation steps and prompt path.
- config/model_api.json: model service connection and timeout settings.
 
## Runtime Contract (Current)
- Cases must include difficulty_spec and model_input.reference_samples.
- expected_output must declare output format and required result fields.
- metrics_inputs should include case_id, case_path, sample_test_timeout_seconds, raw_output_path; optional subtask_count, algorithm_complexity_level, ambiguity_score, semantic_consistency_score, style_score, performance_score, robustness_score.
- metrics_config should define difficulty_metric_weights, quality_metric_weights, difficulty_score_caps, quality_score_caps, difficulty_weight.

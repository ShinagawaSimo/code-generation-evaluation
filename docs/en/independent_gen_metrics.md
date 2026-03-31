# Independent Generation Metrics

## Code Difficulty Metrics

### Input Scale Complexity (Auto)
* Task character length
* Reference code character length
* Reference code function count
* Fields: metrics.difficulty.input_scale.task_char_length / reference_code_char_length / reference_code_function_count
* Function: compute_independent_metrics

### Output Complexity (Auto)
* Output field count
* Output function count
* Return structure nesting depth
* Complex object involvement: class, graph, tree, etc.
* Fields: metrics.difficulty.output_complexity.output_field_count / output_function_count / return_nesting_depth / complex_object_involved
* Function: compute_independent_metrics

### Subtask Count (Estimated, Override Allowed)
* Whether the task can be decomposed into multiple logical steps
* Field: metrics.difficulty.subtask_count
* Function: compute_independent_metrics (override from metrics_inputs.subtask_count or difficulty_spec.subtask_count)

### Algorithm Complexity Level (Estimated, Override Allowed)
* 0: No algorithm, CRUD
* 1: Sorting, traversal, simple recursion
* 2: DP, graph
* 3: Search optimization, NP problems
* Field: metrics.difficulty.algorithm_complexity_level
* Function: compute_independent_metrics (override from metrics_inputs.algorithm_complexity_level or difficulty_spec.algorithm_complexity_level)

### Constraint Complexity (Auto)
* Performance or resource constraints
* Constraint keyword occurrences
* Field: metrics.difficulty.constraint_complexity.keyword_count
* Function: compute_independent_metrics

### Ambiguity
* Multiple possible interpretations or implementations
* Requires additional context or external info
* Needs handling of exceptions or edge cases
* Output variability across multiple LLM runs
* Field: metrics.difficulty.ambiguity
* Function: compute_independent_metrics (override from metrics_inputs.ambiguity_score or difficulty_spec.ambiguity_score)

### Test Difficulty (Auto)
* Sample test count
* Boundary-case ratio
* Fields: metrics.difficulty.test_difficulty.sample_test_count / boundary_case_ratio / input_space_size
* Function: compute_independent_metrics

## Code Quality

### Correctness (Auto)
* Meets functional requirements
* Syntax or logic errors
* Unhandled exceptions or edge cases
* Field: metrics.quality.correctness.build_success / sample_tests_pass / pass
* Function: compute_independent_metrics

### Semantic Consistency
* Future consideration
* LLM-based scoring
* Field: quality.modules.semantic_consistency
* Function: compute_quality (input from metrics_inputs.semantic_consistency_score)

### Structural Quality (Auto)
* Function count penalty
* Average function length
* Maximum nesting depth
* Field: metrics.quality.structure.function_count / avg_function_length / max_nesting_depth
* Function: compute_independent_metrics (raw), compute_quality (module score)

### Readability (Auto)
* Identifier length distribution
* Semantic naming ratio
* Comment density
* Field: metrics.quality.readability.identifier_avg_length / identifier_long_ratio / comment_density
* Function: compute_independent_metrics (raw), compute_quality (module score)

### Style Compliance
* Tool-based or manual scoring
* Field: quality.modules.style_compliance
* Function: compute_quality (input from metrics_inputs.style_score)

### Performance (Hint Extraction)
* Time complexity
* Space complexity
* Fields: metrics.quality.performance.complexity_hints, quality.modules.performance
* Function: compute_independent_metrics (raw hints), compute_quality (score from metrics_inputs.performance_score or hints fallback)

### Robustness and Security
* Future implementation
* Field: quality.modules.robustness_security
* Function: compute_quality (input from metrics_inputs.robustness_score)

## Composite Metrics
### Weighted Score
Score = Q ⋅ (1 + λD)
* D: weighted average of normalized Code Difficulty indicators using difficulty_metric_weights
* Q: weighted average of normalized Code Quality indicators using quality_metric_weights
* λ: difficulty_weight
* Fields: difficulty.comprehensive, quality.comprehensive, final_score
* Functions: compute_difficulty, compute_quality, compute_final_score

### Normalized Quality
Q_norm = Q / Expected(Q | D)

### Bucketed Metrics
* Group by difficulty level and compute pass@K and average Q

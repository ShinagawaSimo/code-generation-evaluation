# 独立生成测评指标

## 代码难度指标

### 输入规模复杂度（自动）
* 任务的字符长度
* 参考代码的字符长度
* 参考代码的函数数量
* 字段：metrics.difficulty.input_scale.task_char_length / reference_code_char_length / reference_code_function_count
* 计算函数：compute_independent_metrics

### 输出复杂度（自动）
* 输出字段数
* 输出函数数
* 返回结构的嵌套深度
* 是否涉及复杂对象：类、图、树等
* 字段：metrics.difficulty.output_complexity.output_field_count / output_function_count / return_nesting_depth / complex_object_involved
* 计算函数：compute_independent_metrics

### 子任务数量（自动估计，可人工覆盖）
* 任务是否可分解为多个逻辑步骤
* 字段：metrics.difficulty.subtask_count
* 计算函数：compute_independent_metrics（可由 metrics_inputs.subtask_count 或 difficulty_spec.subtask_count 覆盖）

### 算法复杂度等级（自动估计，可人工覆盖）
* 0: 无算法 CRUD
* 1: 排序、遍历、简单递归等
* 2: DP、图等
* 3: 搜索优化、NP问题等
* 字段：metrics.difficulty.algorithm_complexity_level
* 计算函数：compute_independent_metrics（可由 metrics_inputs.algorithm_complexity_level 或 difficulty_spec.algorithm_complexity_level 覆盖）

### 约束复杂度（自动）
* 是否存在性能或资源约束
* 出现时间复杂度、memory limit、real_time等关键词约束
* 约束关键词计数
* 字段：metrics.difficulty.constraint_complexity.keyword_count
* 计算函数：compute_independent_metrics

### 歧义性
* 是否存在多个可能的解析或实现
* 是否需要考虑上下文或外部信息
* 是否需要处理异常情况或边界条件
* 多次LLM解析任务->输出差异
* 字段：metrics.difficulty.ambiguity
* 计算函数：compute_independent_metrics（可由 metrics_inputs.ambiguity_score 或 difficulty_spec.ambiguity_score 覆盖）

### 测试难度（自动）
* 测试用例数量
* 边界情况比例
* 字段：metrics.difficulty.test_difficulty.sample_test_count / boundary_case_ratio / input_space_size
* 计算函数：compute_independent_metrics

## 代码质量

### 正确性（自动）
* 代码是否符合功能需求
* 是否存在语法错误或逻辑错误
* 是否存在未处理的异常情况或边界条件
* 字段：metrics.quality.correctness.build_success / sample_tests_pass / pass
* 计算函数：compute_independent_metrics

### 语义一致性
* 后续考虑
* 经由特定LLM评分
* 字段：quality.modules.semantic_consistency
* 计算函数：compute_quality（来源 metrics_inputs.semantic_consistency_score）

### 结构质量（自动）
* 函数数量，过多/过少惩罚
* 平均函数长度
* 最大嵌套深度
* 字段：metrics.quality.structure.function_count / avg_function_length / max_nesting_depth
* 计算函数：compute_independent_metrics（原始值），compute_quality（模块分数）

### 可读性（自动）
* 命名长度分布
* 是否存在语义命名
* 注释密度
* 字段：metrics.quality.readability.identifier_avg_length / identifier_long_ratio / comment_density
* 计算函数：compute_independent_metrics（原始值），compute_quality（模块分数）

### 风格规范
* 工具评分或人工补充
* 字段：quality.modules.style_compliance
* 计算函数：compute_quality（来源 metrics_inputs.style_score）

### 性能（自动提取提示）
* 时间复杂度
* 空间复杂度
* 字段：metrics.quality.performance.complexity_hints，quality.modules.performance
* 计算函数：compute_independent_metrics（提示抽取），compute_quality（来源 metrics_inputs.performance_score 或提示兜底）

### 健壮性 安全性
* 后续实现
* 字段：quality.modules.robustness_security
* 计算函数：compute_quality（来源 metrics_inputs.robustness_score）

## 综合指标
### 加权得分
Score=Q⋅(1+λD)
* D：代码难度模块各指标归一化后按 difficulty_metric_weights 加权平均
* Q：代码质量模块各指标归一化后按 quality_metric_weights 加权平均
* λ：difficulty_weight
* 字段：difficulty.comprehensive、quality.comprehensive、final_score
* 计算函数：compute_difficulty、compute_quality、compute_final_score

### 归一化质量
Q_{norm}​=Q/Expected(Q∣D)

### 分桶指标
* 按难度等级分组，分别计算pass@K和平均的Q等。

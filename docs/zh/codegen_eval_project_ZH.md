 # 代码生成评测项目文档
 
## 项目结构
- config：评测配置与运行参数（eval_pipeline.json、run_cases.json、model_api.json）。
- src/cases：评测案例输入数据。
- src/eval_core：评测流程与指标计算。
- src/data_process：构建、执行与数据读写。
- docs：项目说明与评测规范。
- artifacts/raw_outputs：模型原始输出归档。
- artifacts/results：评测结果归档。

## 当前项目体系（已实现）
- 任务范围：当前主流程聚焦 independent_function_development。
- 目录分层：案例输入在 src/cases，运行结果与原始输出在 artifacts。
- 批量运行：run_cases.json 统一管理案例路径、结果路径、默认指标参数。
- 评测流水线：generate_output → compile_build_check → sample_tests_check → process_metrics_check → difficulty_confirmation → final_score。
- 结果产物：每个案例输出独立 result.json 与 raw_output.txt，便于追溯。

 ## 生成内容测评规范
 
 ### 任务输入与输出
 - 直接输入：提示词、提供的代码/文本及明确指令。
 - 间接输入：任务所需的代码仓上下文与外部知识。
 - 预期输出：正确完成任务应生成的代码、文本、代码修改及必要说明。
 - 实际输出：评测中记录的模型产出与相关结果。
 
 ### 测评原则
 - 与预期输出的一致性：测试通过、文本匹配、位置匹配、语义匹配（hit@k、recall@k）。
 - 实际输出的必要性：与预期不一致但正确且有价值的结果应被认可。
 - 代码质量：规范性、安全性、性能与可维护性。
 - 过程证据：中间结果与过程痕迹的可追溯性。
 
### 难度体系
- 当前 D 来源：完全由“代码难度指标”模块计算并加权汇总。
- 代码难度指标模块：
  - 输入规模复杂度：任务字符长度、参考代码长度、参考函数数。
  - 输出复杂度：输出字段数、输出函数数、返回结构嵌套深度、复杂对象参与。
  - 子任务数量：自动估计，可由案例 difficulty_spec 或 metrics_inputs 覆盖。
  - 算法复杂度等级：自动估计，可由案例 difficulty_spec 或 metrics_inputs 覆盖。
  - 约束复杂度：约束关键词计数。
  - 歧义性：默认 0，可由 ambiguity_score 提供。
  - 测试难度：样例数、边界比例、输入空间规模。
- D 计算方式：各子指标先归一化，再按 difficulty_metric_weights 加权平均得到 difficulty_score_d。
 
### 质量体系
- 代码质量模块：
  - 正确性：基于 build_success 与 sample_tests_pass。
  - 语义一致性：可由 semantic_consistency_score 传入。
  - 结构质量：函数数量、平均函数长度、最大嵌套深度。
  - 可读性：标识符长度统计、语义命名比例、注释密度。
  - 风格规范：style_score。
  - 性能：performance_score 或复杂度提示兜底。
  - 健壮性与安全性：robustness_score。
- Q 计算方式：各质量子指标归一化后按 quality_metric_weights 加权平均得到 quality_score_q。
- 最终得分：Score = Q ⋅ (1 + λD)，其中 λ 为 difficulty_weight。

## 配置说明
- config/run_cases.json：案例路径、结果目录、原始输出目录，以及默认的 metrics_inputs/metrics_config。
- config/eval_pipeline.json：评测步骤编排与提示词路径。
- config/model_api.json：模型服务连接与超时配置。
 
## 运行与配置约定（当前）
- 案例文件：必须提供 difficulty_spec 与 model_input.reference_samples。
- expected_output：需声明输出格式与 result 字段要求（run_records 与 evaluation_result 关键字段）。
- metrics_inputs：建议提供 case_id、case_path、sample_test_timeout_seconds、raw_output_path；可选 subtask_count、algorithm_complexity_level、ambiguity_score、semantic_consistency_score、style_score、performance_score、robustness_score。
- metrics_config：统一配置 difficulty_metric_weights、quality_metric_weights、difficulty_score_caps、quality_score_caps、difficulty_weight。

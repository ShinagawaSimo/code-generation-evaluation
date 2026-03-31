 # 生成内容测评样例数据结构说明
 
 ## 字段定义
 - instance_id：评测样例唯一标识。
 - repo：任务上下文来源代码仓名称。
 - version：任务定义时的代码仓版本。
 - task_type：independent_function_development | new_application_development | incremental_feature_development。
 - language：任务主要编程语言。
 - task_original_statement：原始任务描述，作为主要输入。
 - is_original_task：是否为原始任务描述。
 - task_revision_statement：当难度或范围调整时的修订描述。
 - input_direct：提供给模型的直接输入，包含代码与指令。
 - input_indirect：间接输入，包括代码仓上下文与外部知识。
 - expected_output：正确完成任务的预期产物与验收标准。
 - difficulty_spec：案例级难度覆盖值（subtask_count、algorithm_complexity_level、ambiguity_score）。
 - base_commit：任务基线提交哈希。
 - patch：预期代码变更的diff内容（若适用）。
 - test_setup_id：评测环境配置标识。
 - hints_text：可选提示信息。
 - tags：可选标签，用于批量筛选。
 - metrics_config：指标定义与权重配置（difficulty_metric_weights、quality_metric_weights、difficulty_score_caps、quality_score_caps、difficulty_weight）。
 - metrics_inputs：运行参数与运行时输入（如样例超时、工具回合数、构建路径、raw_output_path，以及可选覆盖值 subtask_count、algorithm_complexity_level、ambiguity_score、semantic_consistency_score、style_score、performance_score、robustness_score）。
 - run_records：执行日志、输出与中间产物。
 - evaluation_result：评分结果、通过性、评审记录与自动化指标汇总（metrics、difficulty、quality、quality_score_q、difficulty_score_d、final_score）。

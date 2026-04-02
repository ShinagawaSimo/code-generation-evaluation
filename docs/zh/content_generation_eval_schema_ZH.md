 # 生成内容测评样例数据结构说明
 
 ## 字段定义
 - instance_id：评测样例唯一标识。
 - task_type：independent_function_development | new_application_development | incremental_feature_development。
 - language：任务主要编程语言。
 - task_original_statement：原始任务描述，作为主要输入。
 - input_direct：提供给模型的直接输入，包含代码与指令。
 - input_indirect：间接输入，包括代码仓上下文与外部知识。
 - expected_output：正确完成任务的预期产物与验收标准。
 - difficulty_spec：案例级难度覆盖值（subtask_count、algorithm_complexity_level、ambiguity_score）。
- model_input：模型输入主体（任务描述、样例、代码骨架）。
- metrics_inputs：运行时输入（如 case_id、case_path 及可选覆盖值 subtask_count、algorithm_complexity_level、ambiguity_score）。

## Result 落盘字段（精简后）
- instance_id：样例唯一标识。
- task_type：任务类型。
- language：语言标识。
- case_path：案例文件路径，用于回溯输入来源。
- run_records：仅保留确定性评测所需记录：
  - build：success、error、workspace、language、source_path、output_path、build_command、run_command、returncode。
  - sample_tests：passed 与每条样例的 input、expected_output、actual_output、returncode、passed。
  - raw_output_path：模型原始输出的文件路径。
  - model_error：模型调用失败或输出异常时的错误信息（若存在）。
- evaluation_result：完整评分结果，包含 metrics、difficulty、quality、quality_score_q、difficulty_score_d、scores、final_score、passed、review_notes。

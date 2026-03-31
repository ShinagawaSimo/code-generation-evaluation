from typing import Tuple, Dict, List
import re

from .models import EvaluationContext


def _text_length(value: str | None) -> int:
    """
    Return length of text input or 0 when empty.
    Args:
        value: Text to measure.
    """
    return len(value) if value else 0


def _combine_reference_code(context: EvaluationContext) -> str:
    """
    Combine provided reference code and code skeleton into a single string.
    Args:
        context: Evaluation context containing input_direct and model_input.
    """
    parts: List[str] = []
    provided = context.input_direct.get("provided_code") if context.input_direct else []
    if isinstance(provided, list):
        parts.extend([str(item) for item in provided if item])
    elif provided:
        parts.append(str(provided))
    code_skeleton = ""
    if context.model_input:
        code_skeleton = context.model_input.get("code_skeleton") or ""
    if code_skeleton:
        parts.append(code_skeleton)
    return "\n".join(parts)


def _count_functions(text: str, language: str) -> int:
    """
    Count function definitions in code text for the given language.
    Args:
        text: Code text to analyze.
        language: Programming language name.
    """
    lang = (language or "").lower()
    lines = text.splitlines()
    count = 0
    if lang == "python":
        for line in lines:
            if re.match(r"^\s*def\s+[A-Za-z_]\w*\s*\(", line):
                count += 1
        return count
    if lang in {"javascript", "typescript"}:
        for line in lines:
            if re.match(r"^\s*function\s+[A-Za-z_]\w*\s*\(", line):
                count += 1
                continue
            if re.match(r"^\s*(const|let|var)\s+[A-Za-z_]\w*\s*=\s*function\s*\(", line):
                count += 1
                continue
            if re.match(r"^\s*(const|let|var)\s+[A-Za-z_]\w*\s*=\s*\(.*\)\s*=>", line):
                count += 1
        return count
    keywords = {"if", "for", "while", "switch", "catch", "return", "sizeof"}
    for line in lines:
        match = re.match(
            r"^\s*(?:public|private|protected)?\s*(?:static\s+)?[\w\<\>\[\]\*&]+\s+([A-Za-z_]\w*)\s*\(",
            line,
        )
        if match and match.group(1) not in keywords:
            count += 1
    return count


def _max_bracket_depth(text: str) -> int:
    """
    Compute maximum bracket nesting depth.
    Args:
        text: Code or text to analyze.
    """
    depth = 0
    max_depth = 0
    for ch in text:
        if ch in "([{":
            depth += 1
            if depth > max_depth:
                max_depth = depth
        elif ch in ")]}":
            depth = max(depth - 1, 0)
    return max_depth


def _max_return_nesting_depth(text: str) -> int:
    """
    Estimate nesting depth near return or yield statements.
    Args:
        text: Code text to analyze.
    """
    max_depth = 0
    for line in text.splitlines():
        if "return" in line or "yield" in line:
            depth = _max_bracket_depth(line)
            if depth > max_depth:
                max_depth = depth
    return max_depth


def _count_output_fields(text: str) -> int:
    """
    Estimate number of returned fields in object/dict literals.
    Args:
        text: Code text to analyze.
    """
    max_fields = 0
    for match in re.finditer(r"return\s*\{([^}]*)\}", text):
        body = match.group(1)
        fields = body.count(":")
        if fields > max_fields:
            max_fields = fields
    for match in re.finditer(r"return\s*dict\(([^)]*)\)", text):
        body = match.group(1)
        fields = 1 + body.count(",") if body.strip() else 0
        if fields > max_fields:
            max_fields = fields
    return max_fields


def _estimate_subtask_count(text: str) -> int:
    """
    Estimate subtask count from task description by separators.
    Args:
        text: Task description text.
    """
    if not text:
        return 0
    lower = text.lower()
    separators = [" and ", " then ", " followed by ", " after ", "并", "然后", "接着", "同时"]
    count = 1
    for sep in separators:
        count += lower.count(sep)
    return count


def _estimate_algorithm_level(text: str) -> int:
    """
    Estimate algorithm complexity level from keywords.
    Args:
        text: Task description text.
    """
    if not text:
        return 0
    lower = text.lower()
    if any(key in lower for key in ["np", "tsp", "sat", "integer programming"]):
        return 3
    if any(
        key in lower
        for key in [
            "dynamic programming",
            "dp",
            "shortest path",
            "graph",
            "bfs",
            "dfs",
            "dijkstra",
            "bellman",
            "topological",
            "segment tree",
            "fenwick",
            "union find",
        ]
    ):
        return 2
    if any(
        key in lower
        for key in ["sort", "sorting", "traverse", "traversal", "binary search", "recursion"]
    ):
        return 1
    return 0


def _constraint_keyword_count(text: str) -> int:
    """
    Count constraint-related keywords in task description.
    Args:
        text: Task description text.
    """
    if not text:
        return 0
    lower = text.lower()
    keywords = ["time", "memory", "limit", "complexity", "o(", "constraints", "n up to"]
    return sum(lower.count(key) for key in keywords)


def _boundary_case_ratio(samples: List[Dict[str, str]]) -> float:
    """
    Estimate boundary case ratio from sample inputs.
    Args:
        samples: Sample input/output pairs.
    """
    if not samples:
        return 0.0
    boundary = 0
    for sample in samples:
        content = (sample.get("input") or sample.get("stdin") or "").strip()
        tokens = content.replace("\n", " ").split()
        if any(token in {"0", "1"} or token.startswith("-") for token in tokens):
            boundary += 1
    return boundary / len(samples)


def _function_lengths(text: str, language: str) -> List[int]:
    """
    Estimate function lengths in lines for the given language.
    Args:
        text: Code text to analyze.
        language: Programming language name.
    """
    lines = text.splitlines()
    lang = (language or "").lower()
    lengths: List[int] = []
    if lang == "python":
        indices: List[tuple[int, int]] = []
        for idx, line in enumerate(lines):
            if re.match(r"^\s*def\s+[A-Za-z_]\w*\s*\(", line):
                indent = len(line) - len(line.lstrip(" \t"))
                indices.append((idx, indent))
        for i, (start, indent) in enumerate(indices):
            end = len(lines)
            for j in range(start + 1, len(lines)):
                if re.match(
                    r"^\s*(def\s+[A-Za-z_]\w*\s*\(|class\s+[A-Za-z_]\w*)",
                    lines[j],
                ) and (len(lines[j]) - len(lines[j].lstrip(" \t")) <= indent):
                    end = j
                    break
            length = sum(1 for line in lines[start:end] if line.strip())
            lengths.append(length)
        return lengths
    for idx, line in enumerate(lines):
        match = re.match(
            r"^\s*(?:public|private|protected)?\s*(?:static\s+)?[\w\<\>\[\]\*&]+\s+[A-Za-z_]\w*\s*\(",
            line,
        )
        if not match:
            continue
        depth = 0
        end = None
        for j in range(idx, len(lines)):
            depth += lines[j].count("{")
            depth -= lines[j].count("}")
            if depth > 0 and end is None:
                end = j
            if depth == 0 and end is not None:
                end = j + 1
                break
        if end:
            length = sum(1 for line in lines[idx:end] if line.strip())
            lengths.append(length)
    return lengths


def _max_nesting_depth(text: str, language: str) -> int:
    """
    Estimate maximum nesting depth for the given language.
    Args:
        text: Code text to analyze.
        language: Programming language name.
    """
    lang = (language or "").lower()
    if lang == "python":
        max_indent = 0
        for line in text.splitlines():
            if not line.strip():
                continue
            prefix = re.match(r"^[ \t]*", line).group(0)
            indent = prefix.count(" ") + prefix.count("\t") * 4
            if indent > max_indent:
                max_indent = indent
        return max_indent // 4 if max_indent > 0 else 0
    return _max_bracket_depth(text)


def _comment_density(text: str, language: str) -> float:
    """
    Estimate comment line ratio in code.
    Args:
        text: Code text to analyze.
        language: Programming language name.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    lang = (language or "").lower()
    comment = 0
    for line in lines:
        stripped = line.strip()
        if lang == "python":
            if stripped.startswith("#"):
                comment += 1
        else:
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                comment += 1
    return comment / len(lines)


def _identifier_stats(text: str) -> Dict[str, float]:
    """
    Compute identifier length statistics.
    Args:
        text: Code text to analyze.
    """
    identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
    keywords = {
        "if",
        "else",
        "for",
        "while",
        "switch",
        "case",
        "break",
        "continue",
        "return",
        "class",
        "def",
        "public",
        "private",
        "protected",
        "static",
        "import",
        "from",
        "try",
        "except",
        "finally",
        "true",
        "false",
        "null",
        "none",
        "void",
        "int",
        "float",
        "double",
        "string",
        "bool",
        "new",
    }
    filtered = [ident for ident in identifiers if ident.lower() not in keywords]
    if not filtered:
        return {"avg_length": 0.0, "long_ratio": 0.0}
    lengths = [len(ident) for ident in filtered]
    avg_length = sum(lengths) / len(lengths)
    long_ratio = sum(1 for length in lengths if length >= 3) / len(lengths)
    return {"avg_length": avg_length, "long_ratio": long_ratio}


def compute_independent_metrics(context: EvaluationContext) -> Dict[str, object]:
    """
    Compute automated metrics for independent generation tasks.
    Args:
        context: Evaluation context with model inputs and run records.
    """
    task_text = (
        (context.model_input.get("task_description") if context.model_input else None)
        or context.task_original_statement
        or ""
    )
    reference_code = _combine_reference_code(context)
    output_text = context.run_records.get("raw_output", "") or ""
    samples = context.model_input.get("reference_samples") or []
    language = context.language or ""
    profile = context.difficulty_spec or {}
    subtask_override = context.metrics_inputs.get("subtask_count", profile.get("subtask_count"))
    alg_override = context.metrics_inputs.get(
        "algorithm_complexity_level",
        profile.get("algorithm_complexity_level"),
    )
    ambiguity_override = context.metrics_inputs.get("ambiguity_score", profile.get("ambiguity_score"))
    style_score = context.metrics_inputs.get("style_score")
    robustness_score = context.metrics_inputs.get("robustness_score")
    complexity_hints = re.findall(r"O\([^)]*\)", task_text + "\n" + output_text)
    id_stats = _identifier_stats(output_text)
    function_lengths = _function_lengths(output_text, language)
    input_space_size = sum(
        len((sample.get("input") or sample.get("stdin") or "").strip().split())
        for sample in samples
    )
    return {
        "difficulty": {
            "input_scale": {
                "task_char_length": _text_length(task_text),
                "reference_code_char_length": _text_length(reference_code),
                "reference_code_function_count": _count_functions(reference_code, language),
            },
            "output_complexity": {
                "output_field_count": _count_output_fields(output_text),
                "output_function_count": _count_functions(output_text, language),
                "return_nesting_depth": _max_return_nesting_depth(output_text),
                "complex_object_involved": any(
                    key in output_text.lower()
                    for key in ["class", "struct", "tree", "graph", "trie", "heap", "node"]
                ),
            },
            "subtask_count": int(subtask_override)
            if subtask_override is not None
            else _estimate_subtask_count(task_text),
            "algorithm_complexity_level": int(alg_override)
            if alg_override is not None
            else _estimate_algorithm_level(task_text),
            "constraint_complexity": {
                "keyword_count": _constraint_keyword_count(task_text),
            },
            "ambiguity": ambiguity_override,
            "test_difficulty": {
                "sample_test_count": len(samples),
                "boundary_case_ratio": _boundary_case_ratio(samples),
                "input_space_size": input_space_size,
            },
        },
        "quality": {
            "correctness": {
                "build_success": bool(context.metrics_inputs.get("build_success")),
                "sample_tests_pass": bool(context.metrics_inputs.get("sample_tests_pass")),
                "pass": bool(context.metrics_inputs.get("build_success"))
                and bool(context.metrics_inputs.get("sample_tests_pass")),
            },
            "structure": {
                "function_count": _count_functions(output_text, language),
                "avg_function_length": sum(function_lengths) / len(function_lengths)
                if function_lengths
                else 0.0,
                "max_nesting_depth": _max_nesting_depth(output_text, language),
            },
            "readability": {
                "identifier_avg_length": id_stats["avg_length"],
                "identifier_long_ratio": id_stats["long_ratio"],
                "comment_density": _comment_density(output_text, language),
            },
            "style": {"score": style_score},
            "performance": {"complexity_hints": list(dict.fromkeys(complexity_hints))},
            "robustness_security": {"score": robustness_score},
        },
    }


def _weighted_average(values: Dict[str, float], weights: Dict[str, float]) -> float:
    total_weight = 0.0
    weighted_sum = 0.0
    for key, value in values.items():
        weight = float(weights.get(key, 1.0))
        if weight <= 0:
            continue
        total_weight += weight
        weighted_sum += float(value) * weight
    if total_weight <= 0:
        return 0.0
    return weighted_sum / total_weight


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_ratio(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return _clamp01(float(value) / float(cap))


def evaluate_build(context: EvaluationContext) -> Tuple[float, bool]:
    """
    Compute build score and success flag from metrics inputs.
    context: evaluation context providing build_success and weights.
    """
    build_success = bool(context.metrics_inputs.get("build_success", True))
    weight = context.metrics_config.get("build_weight", 1.0)
    return (weight if build_success else -weight), build_success


def evaluate_process_metrics(context: EvaluationContext) -> float:
    """
    Score process metrics based on explicit flag or thresholds.
    context: evaluation context with metrics inputs and thresholds.
    """
    explicit_ok = context.metrics_inputs.get("process_metrics_ok")
    if explicit_ok is not None:
        within_bounds = bool(explicit_ok)
    else:
        response_time_ms = context.metrics_inputs.get("response_time_ms")
        token_usage = context.metrics_inputs.get("token_usage")
        cost_usd = context.metrics_inputs.get("cost_usd")
        max_response_time_ms = context.metrics_config.get("max_response_time_ms")
        max_token_usage = context.metrics_config.get("max_token_usage")
        max_cost_usd = context.metrics_config.get("max_cost_usd")
        checks = []
        if max_response_time_ms is not None and response_time_ms is not None:
            checks.append(float(response_time_ms) <= float(max_response_time_ms))
        if max_token_usage is not None and token_usage is not None:
            checks.append(int(token_usage) <= int(max_token_usage))
        if max_cost_usd is not None and cost_usd is not None:
            checks.append(float(cost_usd) <= float(max_cost_usd))
        within_bounds = all(checks) if checks else True
    weight = context.metrics_config.get("process_weight", 1.0)
    return weight if within_bounds else -weight


def evaluate_sample_tests(context: EvaluationContext) -> Tuple[float, bool]:
    """
    Score sample test results and return pass flag.
    context: evaluation context with sample_tests_pass and weight.
    """
    passed = bool(context.metrics_inputs.get("sample_tests_pass", False))
    weight = context.metrics_config.get("sample_tests_weight", 1.0)
    return (weight if passed else -weight), passed


def compute_difficulty(context: EvaluationContext) -> Dict[str, object]:
    computed = context.evaluation_result.get("metrics") or compute_independent_metrics(context)
    difficulty = computed.get("difficulty", {})
    score_caps = context.metrics_config.get("difficulty_score_caps", {})
    module_weights = context.metrics_config.get("difficulty_metric_weights", {})
    profile = context.difficulty_spec or {}
    ambiguity_override = context.metrics_inputs.get("ambiguity_score", profile.get("ambiguity_score", 0.0))
    input_scale_data = difficulty.get("input_scale", {})
    input_scale_score = _weighted_average(
        {
            "task_char_length": _safe_ratio(
                float(input_scale_data.get("task_char_length", 0)),
                float(score_caps.get("task_char_length", 2000)),
            ),
            "reference_code_char_length": _safe_ratio(
                float(input_scale_data.get("reference_code_char_length", 0)),
                float(score_caps.get("reference_code_char_length", 2000)),
            ),
            "reference_code_function_count": _safe_ratio(
                float(input_scale_data.get("reference_code_function_count", 0)),
                float(score_caps.get("reference_code_function_count", 10)),
            ),
        },
        context.metrics_config.get("input_scale_weights", {}),
    )
    output_complexity_data = difficulty.get("output_complexity", {})
    output_complexity_score = _weighted_average(
        {
            "output_field_count": _safe_ratio(
                float(output_complexity_data.get("output_field_count", 0)),
                float(score_caps.get("output_field_count", 8)),
            ),
            "output_function_count": _safe_ratio(
                float(output_complexity_data.get("output_function_count", 0)),
                float(score_caps.get("output_function_count", 12)),
            ),
            "return_nesting_depth": _safe_ratio(
                float(output_complexity_data.get("return_nesting_depth", 0)),
                float(score_caps.get("return_nesting_depth", 6)),
            ),
            "complex_object_involved": 1.0 if output_complexity_data.get("complex_object_involved") else 0.0,
        },
        context.metrics_config.get("output_complexity_weights", {}),
    )
    subtask_count = float(difficulty.get("subtask_count", 0))
    algorithm_level = float(difficulty.get("algorithm_complexity_level", 0))
    constraint_count = float((difficulty.get("constraint_complexity") or {}).get("keyword_count", 0))
    test_data = difficulty.get("test_difficulty", {})
    test_difficulty_score = _weighted_average(
        {
            "sample_test_count": _safe_ratio(
                float(test_data.get("sample_test_count", 0)),
                float(score_caps.get("sample_test_count", 10)),
            ),
            "boundary_case_ratio": _clamp01(float(test_data.get("boundary_case_ratio", 0.0))),
            "input_space_size": _safe_ratio(
                float(test_data.get("input_space_size", 0)),
                float(score_caps.get("input_space_size", 200)),
            ),
        },
        context.metrics_config.get("test_difficulty_weights", {}),
    )
    module_scores = {
        "input_scale_complexity": input_scale_score,
        "output_complexity": output_complexity_score,
        "subtask_count": _safe_ratio(subtask_count, float(score_caps.get("subtask_count", 8))),
        "algorithm_complexity_level": _safe_ratio(
            algorithm_level,
            float(score_caps.get("algorithm_complexity_level", 3)),
        ),
        "constraint_complexity": _safe_ratio(
            constraint_count,
            float(score_caps.get("constraint_keyword_count", 10)),
        ),
        "ambiguity": _clamp01(float(ambiguity_override or 0.0)),
        "test_difficulty": test_difficulty_score,
    }
    comprehensive = _weighted_average(module_scores, module_weights)
    override = context.metrics_inputs.get("difficulty_score_override")
    if override is not None:
        comprehensive = _clamp01(float(override))
    return {
        "modules": module_scores,
        "comprehensive": comprehensive,
        "raw": difficulty,
    }


def compute_quality(context: EvaluationContext) -> Dict[str, object]:
    computed = context.evaluation_result.get("metrics") or compute_independent_metrics(context)
    quality = computed.get("quality", {})
    caps = context.metrics_config.get("quality_score_caps", {})
    module_weights = context.metrics_config.get("quality_metric_weights", {})
    correctness = quality.get("correctness", {})
    correctness_score = 1.0 if correctness.get("pass") else 0.0
    structure = quality.get("structure", {})
    structure_score = _weighted_average(
        {
            "function_count": 1.0
            - _safe_ratio(
                abs(float(structure.get("function_count", 0)) - float(caps.get("target_function_count", 4))),
                float(caps.get("target_function_count", 4)),
            ),
            "avg_function_length": 1.0
            - _safe_ratio(
                abs(float(structure.get("avg_function_length", 0)) - float(caps.get("target_avg_function_length", 20))),
                float(caps.get("target_avg_function_length", 20)),
            ),
            "max_nesting_depth": 1.0
            - _safe_ratio(
                max(0.0, float(structure.get("max_nesting_depth", 0)) - float(caps.get("target_max_nesting_depth", 4))),
                float(caps.get("target_max_nesting_depth", 4)),
            ),
        },
        context.metrics_config.get("structure_quality_weights", {}),
    )
    readability = quality.get("readability", {})
    readability_score = _weighted_average(
        {
            "identifier_avg_length": _safe_ratio(
                float(readability.get("identifier_avg_length", 0.0)),
                float(caps.get("target_identifier_avg_length", 12)),
            ),
            "identifier_long_ratio": _clamp01(float(readability.get("identifier_long_ratio", 0.0))),
            "comment_density": _safe_ratio(
                float(readability.get("comment_density", 0.0)),
                float(caps.get("target_comment_density", 0.2)),
            ),
        },
        context.metrics_config.get("readability_weights", {}),
    )
    semantic_consistency = context.metrics_inputs.get("semantic_consistency_score", 0.0)
    style_score = quality.get("style", {}).get("score")
    performance_score = context.metrics_inputs.get("performance_score")
    if performance_score is None:
        hints = quality.get("performance", {}).get("complexity_hints", [])
        performance_score = 1.0 if hints else 0.5
    robustness_score = quality.get("robustness_security", {}).get("score")
    module_scores = {
        "correctness": correctness_score,
        "semantic_consistency": _clamp01(float(semantic_consistency or 0.0)),
        "structure_quality": _clamp01(structure_score),
        "readability": _clamp01(readability_score),
        "style_compliance": _clamp01(float(style_score if style_score is not None else 0.0)),
        "performance": _clamp01(float(performance_score)),
        "robustness_security": _clamp01(float(robustness_score if robustness_score is not None else 0.0)),
    }
    comprehensive = _weighted_average(module_scores, module_weights)
    return {
        "modules": module_scores,
        "comprehensive": comprehensive,
        "raw": quality,
    }


def compute_final_score(context: EvaluationContext) -> float:
    quality = context.evaluation_result.get("quality", {})
    difficulty = context.evaluation_result.get("difficulty", {})
    quality_score = float(quality.get("comprehensive", 0.0))
    difficulty_score = float(difficulty.get("comprehensive", 0.0))
    difficulty_weight = float(context.metrics_config.get("difficulty_weight", 0.2))
    return quality_score * (1.0 + difficulty_weight * difficulty_score)

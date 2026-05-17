import ast
import io
import re
import tokenize
from pathlib import Path
from typing import Any, Dict, List

from .models import CodeMetricsResult


def _compute_comment_ratio_python(code_text: str) -> float:
    total_lines = len(code_text.splitlines())
    if total_lines == 0:
        return 0.0
    comment_lines = 0
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code_text).readline))
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comment_lines += 1
    except tokenize.TokenError:
        pass
    try:
        tree = ast.parse(code_text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    comment_lines += len(docstring.splitlines())
    except SyntaxError:
        pass
    total = max(total_lines, 1)
    return min(comment_lines / total, 1.0)


def _compute_comment_ratio_regex(code_text: str) -> float:
    total_lines = len(code_text.splitlines())
    if total_lines == 0:
        return 0.0
    comment_lines = 0
    in_block_comment = False
    for line in code_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if in_block_comment:
            comment_lines += 1
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("//") or stripped.startswith("#"):
            comment_lines += 1
        elif stripped.startswith("/*"):
            comment_lines += 1
            if "*/" not in stripped:
                in_block_comment = True
        elif stripped.startswith("*") and not stripped.startswith("**"):
            comment_lines += 1
    return min(comment_lines / total_lines, 1.0)


def _compute_comment_ratio(code_text: str, language: str) -> float:
    if language == "python":
        return _compute_comment_ratio_python(code_text)
    return _compute_comment_ratio_regex(code_text)


def _compute_codebleu(reference_text: str, generated_text: str, language: str) -> float:
    try:
        from codebleu import calc_codebleu

        lang_map = {
            "python": "python",
            "java": "java",
            "javascript": "javascript",
            "js": "javascript",
            "typescript": "typescript",
            "ts": "typescript",
            "cpp": "cpp",
            "c": "c",
            "csharp": "csharp",
            "go": "go",
            "rust": "rust",
        }
        lang = lang_map.get(language.lower(), "python")
        result = calc_codebleu([reference_text], [generated_text], lang=lang)
        if isinstance(result, dict):
            return float(result.get("codebleu", 0.0))
        return float(result.codebleu)
    except ImportError:
        return 0.0
    except Exception:
        return 0.0


def _compute_codebleu_vs_references(
    generated_code_text: str,
    ref_result: Dict[str, Any],
    language: str,
) -> Dict[str, Any]:
    implementations = ref_result.get("reference_implementations", [])
    if not implementations:
        return {"max_score": 0.0, "best_approach_id": "", "per_approach": []}

    per_approach: List[Dict[str, Any]] = []
    for impl in implementations:
        code_file_path = impl.get("code_file_path", "")
        if not code_file_path or not Path(code_file_path).exists():
            continue
        ref_text = Path(code_file_path).read_text(encoding="utf-8")
        score = _compute_codebleu(ref_text, generated_code_text, language)
        per_approach.append({
            "approach_id": impl.get("approach_id", ""),
            "approach_name": impl.get("approach_name", ""),
            "codebleu_score": score,
        })

    if not per_approach:
        return {"max_score": 0.0, "best_approach_id": "", "per_approach": []}

    best = max(per_approach, key=lambda x: x["codebleu_score"])
    return {
        "max_score": best["codebleu_score"],
        "best_approach_id": best["approach_id"],
        "per_approach": per_approach,
    }


def evaluate_code_metrics(
    task_id: str,
    code_gen_result: Dict[str, Any],
    exec_result: Dict[str, Any],
    ref_result: Dict[str, Any],
) -> CodeMetricsResult:
    compile_success = bool(exec_result.get("compile_success", False))
    run_success = bool(exec_result.get("run_success", True))

    passed = int(exec_result.get("passed_test_count", 0))
    failed = int(exec_result.get("failed_test_count", 0))
    total = passed + failed
    pass_rate = round(passed / max(total, 1), 4) if total > 0 else 0.0
    test_results = {
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
    }

    code_file_path = str(code_gen_result.get("code_file_path", ""))
    generated_code_text = ""
    if code_file_path and Path(code_file_path).exists():
        generated_code_text = Path(code_file_path).read_text(encoding="utf-8")
    language = str(code_gen_result.get("language", ""))

    codebleu = _compute_codebleu_vs_references(generated_code_text, ref_result, language)

    inference_time_seconds = float(code_gen_result.get("inference_time_seconds", 0.0))
    prompt_tokens = int(code_gen_result.get("prompt_tokens", 0))
    completion_tokens = int(code_gen_result.get("completion_tokens", 0))
    total_tokens = prompt_tokens + completion_tokens

    comment_ratio = _compute_comment_ratio(generated_code_text, language)

    return CodeMetricsResult(
        task_id=task_id,
        compile_success=compile_success,
        run_success=run_success,
        compile_runtime_success=compile_success and run_success,
        test_results=test_results,
        codebleu=codebleu,
        inference_time_seconds=inference_time_seconds,
        total_tokens=total_tokens,
        comment_ratio=comment_ratio,
    )

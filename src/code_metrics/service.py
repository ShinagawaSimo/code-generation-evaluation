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


def _load_test_report(artifacts_dir: str, task_id: str) -> List[Dict[str, Any]]:
    report_path = Path(artifacts_dir) / task_id / "test_report.json"
    if not report_path.exists():
        return []
    import json
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("results", [])


def _build_category_map(spec_result: Dict[str, Any], test_result: Dict[str, Any]) -> Dict[str, str]:
    category_map: Dict[str, str] = {}
    for point in spec_result.get("requirement_points", []):
        pid = point.get("point_id", "")
        cat = point.get("category", "basic_function")
        if pid:
            category_map[pid] = cat
    for spec in test_result.get("point_specs", []):
        pid = spec.get("point_id", "")
        cat = spec.get("category", "")
        if pid and cat:
            category_map[pid] = cat
    return category_map


def _categorize_test_results(
    test_report_results: List[Dict[str, Any]],
    category_map: Dict[str, str],
) -> Dict[str, Any]:
    cat_groups: Dict[str, Dict[str, int]] = {}
    per_point: List[Dict[str, Any]] = []
    for tr in test_report_results:
        pid = tr.get("point_id", "")
        passed = tr.get("passed", False)
        category = category_map.get(pid, "unknown")
        cat = category.replace("_function", "").replace("_non_function", "").replace("basic_", "").replace("optional_", "").replace("implicit_", "")
        if cat not in cat_groups:
            cat_groups[cat] = {"passed": 0, "failed": 0, "total": 0}
        if passed:
            cat_groups[cat]["passed"] += 1
        else:
            cat_groups[cat]["failed"] += 1
        cat_groups[cat]["total"] += 1
        per_point.append({
            "point_id": pid,
            "category": category,
            "passed": passed,
        })

    functional_cats = {"basic_function", "implicit_function"}
    non_functional_cats = {"basic_non_function", "optional_non_function", "optional_function"}
    func_passed = 0
    func_total = 0
    nonfunc_passed = 0
    nonfunc_total = 0
    all_passed = 0
    all_total = 0
    for pid, cat in category_map.items():
        tr_match = next((tr for tr in test_report_results if tr.get("point_id") == pid), None)
        if tr_match is None:
            continue
        passed = tr_match.get("passed", False)
        all_total += 1
        if passed:
            all_passed += 1
        if cat in functional_cats:
            func_total += 1
            if passed:
                func_passed += 1
        elif cat in non_functional_cats:
            nonfunc_total += 1
            if passed:
                nonfunc_passed += 1

    cat_details = {}
    for key, group in sorted(cat_groups.items()):
        cat_details[key] = {
            "passed": group["passed"],
            "failed": group["failed"],
            "pass_rate": round(group["passed"] / max(group["total"], 1), 4),
        }

    return {
        "overall": {
            "passed": all_passed,
            "failed": all_total - all_passed,
            "pass_rate": round(all_passed / max(all_total, 1), 4),
        },
        "functional": {
            "passed": func_passed,
            "failed": func_total - func_passed,
            "pass_rate": round(func_passed / max(func_total, 1), 4),
        },
        "non_functional": {
            "passed": nonfunc_passed,
            "failed": nonfunc_total - nonfunc_passed,
            "pass_rate": round(nonfunc_passed / max(nonfunc_total, 1), 4),
        },
        "by_category": cat_details,
        "points": per_point,
    }


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
    spec_result: Dict[str, Any],
    test_gen_result: Dict[str, Any],
    execution_artifacts_dir: str,
) -> CodeMetricsResult:
    compile_success = bool(exec_result.get("compile_success", False))
    run_success = bool(exec_result.get("run_success", False))
    compile_runtime_success = compile_success and run_success

    test_report_results = _load_test_report(execution_artifacts_dir, task_id)
    category_map = _build_category_map(spec_result, test_gen_result)
    test_results = _categorize_test_results(test_report_results, category_map)

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
        compile_runtime_success=compile_runtime_success,
        test_results=test_results,
        codebleu=codebleu,
        inference_time_seconds=inference_time_seconds,
        total_tokens=total_tokens,
        comment_ratio=comment_ratio,
    )

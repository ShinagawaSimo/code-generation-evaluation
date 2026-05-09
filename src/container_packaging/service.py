import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .models import ContainerPackagingResult


def _docker_base_image(language: str) -> str:
    return {
        "c": "gcc:14",
        "cpp": "gcc:14",
        "python": "python:3.11",
        "java": "eclipse-temurin:21",
        "rust": "rust:1.77",
        "go": "golang:1.22",
        "typescript": "node:20",
        "javascript": "node:20",
    }[language]


def _render_dockerfile(language: str, code_filename: str) -> str:
    install_lines: List[str] = []
    if language != "python":
        install_lines.append("RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*")
    if language == "typescript":
        install_lines.append("RUN npm install -g typescript")
    install = ""
    if install_lines:
        install = "\n".join(install_lines) + "\n"
    return (
        f"FROM {_docker_base_image(language)}\n"
        "WORKDIR /workspace\n"
        f"{install}"
        "COPY . /workspace\n"
        'CMD ["python3", "/workspace/scripts/run_packaged_evaluation.py"]\n'
    )


def _render_manifest(
    codegen_result: Dict[str, Any],
    testgen_result: Dict[str, Any],
    packaged_tests_dir: str,
    packaged_point_count: int,
) -> str:
    point_specs = testgen_result["point_specs"]
    return json.dumps(
        {
            "task_id": codegen_result["task_id"],
            "language": codegen_result["language"],
            "code_file_path": codegen_result["code_file_path"],
            "code_filename": Path(str(codegen_result["code_file_path"])).name,
            "test_point_count": len(point_specs),
            "packaged_point_count": packaged_point_count,
            "test_modes": [point["execution_mode"] for point in point_specs],
            "generated_test_files": testgen_result["generated_files"],
            "packaged_tests_dir": packaged_tests_dir,
        },
        ensure_ascii=False,
        indent=2,
    )


def _render_compile_script(language: str, code_filename: str) -> str:
    if language == "c":
        return f"mkdir -p build && gcc -O2 -o build/solution code/{code_filename}\n"
    if language == "cpp":
        return f"mkdir -p build && g++ -O2 -std=c++17 -o build/solution code/{code_filename}\n"
    if language == "rust":
        return f"mkdir -p build && rustc code/{code_filename} -O -o build/solution\n"
    if language == "go":
        return f"mkdir -p build && go build -o build/solution code/{code_filename}\n"
    if language == "java":
        return f"mkdir -p build && javac -d build code/{code_filename}\n"
    if language == "typescript":
        return f"mkdir -p build && tsc code/{code_filename} --outDir build\n"
    if language == "python":
        return f"python3 -m py_compile code/{code_filename}\n"
    if language == "javascript":
        return f"node --check code/{code_filename}\n"
    raise ValueError(f"Unsupported compile language: {language}")


def _render_run_all_tests(language: str, code_filename: str) -> str:
    return "\n".join(
        [
            "#!/bin/sh",
            "python3 /workspace/scripts/run_packaged_evaluation.py",
        ]
    ) + "\n"


def _render_python_test_runner() -> str:
    return """import ast
import importlib.util
import inspect
import json
import random
import subprocess
import sys
import time
import types
from collections import Counter
from pathlib import Path
from typing import get_type_hints

WORKSPACE = Path("/workspace")
TESTS_DIR = WORKSPACE / "tests"
CODE_DIR = WORKSPACE / "code"
BUILD_DIR = WORKSPACE / "build"
REPORT_PATH = WORKSPACE / "test_report.json"
CODE_FILE = sorted(path for path in CODE_DIR.iterdir() if path.is_file())[0]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_text(text: object) -> str:
    return str(text).replace("\\r\\n", "\\n").rstrip()


def _completed_record(completed: subprocess.CompletedProcess[str]) -> dict:
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _program_command(language: str) -> list[str]:
    if language == "python":
        return ["python3", str(CODE_FILE)]
    if language == "javascript":
        return ["node", str(CODE_FILE)]
    if language == "typescript":
        return ["node", str(BUILD_DIR / f"{CODE_FILE.stem}.js")]
    if language in {"c", "cpp", "rust", "go"}:
        return [str(BUILD_DIR / "solution")]
    if language == "java":
        return ["java", "-cp", str(BUILD_DIR), CODE_FILE.stem]
    raise ValueError(f"Unsupported program_io language: {language}")


def _compare_value(actual: object, expected: object, comparator: str) -> bool:
    if comparator in {"equals", "==", "json_equals"}:
        return actual == expected
    if comparator in {"exact_match", "equality"}:
        return actual == expected
    if comparator == "element_counts_match":
        return Counter(actual) == Counter(expected)
    if comparator == "multiset_equals":
        return Counter(actual) == Counter(expected)
    if comparator in {"contains", "text_contains"}:
        return str(expected) in str(actual)
    if comparator == "not_empty":
        return bool(actual)
    return actual == expected


def _extract_behavior_case(assertion: dict) -> dict:
    value = assertion.get("value", {})
    if not isinstance(value, dict):
        value = {}
    args = value.get("arguments", value.get("args", []))
    if args is None:
        args = []
    if not isinstance(args, list):
        args = [args]
    kwargs = value.get("keyword_arguments", value.get("kwargs", {}))
    if not isinstance(kwargs, dict):
        kwargs = {}
    expected = value.get("expected")
    if expected is None:
        expected = value.get("expected_output")
    if expected is None:
        expected = value.get("expected_value")
    comparator = str(value.get("comparator", "equals"))
    return {
        "assertion_id": assertion.get("assertion_id", ""),
        "description": assertion.get("description", ""),
        "args": args,
        "kwargs": kwargs,
        "expected": expected,
        "comparator": comparator,
    }


def _safe_literal_eval(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


def _normalize_call_spec(value: dict) -> dict:
    args = []
    kwargs = {}
    expected = value.get("expected")
    comparator = str(value.get("comparator", value.get("check", value.get("test_type", "equals"))))
    if expected is None:
        expected = value.get("expected_output")

    if "call_args" in value:
        call_args = value.get("call_args", {})
        if isinstance(call_args, dict):
            kwargs = dict(call_args)

    input_spec = value.get("input")
    if isinstance(input_spec, dict):
        if isinstance(input_spec.get("args"), list):
            args = list(input_spec.get("args", []))
        if isinstance(input_spec.get("kwargs"), dict):
            kwargs.update(input_spec.get("kwargs", {}))
    elif isinstance(input_spec, list):
        args = list(input_spec)
    elif input_spec is not None:
        args = [input_spec]

    call_spec = value.get("call", {})
    if isinstance(call_spec, dict):
        if expected is None and "expected" in call_spec:
            expected = call_spec.get("expected")
        call_args = call_spec.get("args")
        if isinstance(call_args, list):
            args = list(call_args)
        elif isinstance(call_args, dict):
            kwargs.update(call_args)

    if not args and "arguments" in value and isinstance(value.get("arguments"), list):
        args = list(value.get("arguments", []))
    if not args and "args" in value and isinstance(value.get("args"), list):
        args = list(value.get("args", []))
    if not kwargs and "kwargs" in value and isinstance(value.get("kwargs"), dict):
        kwargs = dict(value.get("kwargs", {}))
    if not args and "input" in value and isinstance(value.get("input"), list):
        args = list(value.get("input", []))
    if not args and "input" in value and not isinstance(value.get("input"), dict):
        args = [value.get("input")]
    if isinstance(value.get("params"), dict):
        kwargs.update(value.get("params", {}))

    args = [_safe_literal_eval(item) for item in args]
    kwargs = {str(key): _safe_literal_eval(item) for key, item in kwargs.items()}
    expected = _safe_literal_eval(expected)
    return {
        "args": args,
        "kwargs": kwargs,
        "expected": expected,
        "comparator": comparator,
    }


def _call_python_function(function, kwargs: dict, args: list[object]) -> tuple[object, list[object], str]:
    ordered_kwargs = dict(kwargs)
    positional_args = list(args)
    list_like_keys = [key for key, value in ordered_kwargs.items() if isinstance(value, list)]
    if not positional_args and list_like_keys:
        first_key = list_like_keys[0]
        positional_args.append(ordered_kwargs.pop(first_key))
    try:
        return function(*positional_args, **ordered_kwargs), positional_args, ""
    except TypeError as error:
        if kwargs and not args:
            try:
                return function(*list(kwargs.values())), list(kwargs.values()), ""
            except Exception:
                return None, positional_args, str(error)
        return None, positional_args, str(error)


def _run_python_exec_assertion(assertion: dict, function, entry_name: str) -> dict:
    namespace = {"__builtins__": __builtins__, entry_name: function}
    value = assertion.get("value", {})
    try:
        for alias in ["module", "solution", "sort_module"]:
            module = types.ModuleType(alias)
            setattr(module, entry_name, function)
            sys.modules[alias] = module
        setup = value.get("setup", "")
        pre_call = value.get("pre_call", "")
        if setup:
            exec(setup, namespace, namespace)
        if pre_call:
            exec(pre_call, namespace, namespace)
        test_code = value.get("test_code", "")
        if test_code:
            exec(test_code, namespace, namespace)
        post_call_check = value.get("post_call_check", "")
        if post_call_check:
            if value.get("inputs") and entry_name not in post_call_check and "result" not in namespace:
                call_args = [_safe_literal_eval(item) for item in value.get("inputs", [])]
                namespace["result"] = function(*call_args)
            exec(post_call_check, namespace, namespace)
        return {
            "status": "passed",
            "actual": namespace.get("result"),
            "expected": None,
            "stderr": "",
            "reason": "executed_python_snippet",
        }
    except Exception as error:
        return {
            "status": "failed",
            "actual": None,
            "expected": None,
            "stderr": str(error),
            "reason": "python_snippet_failed",
        }


def _run_python_type_hint_assertion(assertion: dict, function) -> dict:
    expectation = assertion.get("expectation", {})
    value = assertion.get("value", {})
    expected = expectation.get("expected", value.get("expected", {}))
    if not isinstance(expected, dict):
        return {"status": "skipped", "reason": "invalid_type_hint_expectation", "stderr": ""}
    hints = get_type_hints(function)
    signature = inspect.signature(function)
    try:
        parameter_hints = {key: value for key, value in hints.items() if key != "return"}
        passed = True
        for name, expected_hint in expected.items():
            if name == "return":
                continue
            actual_hint = hints.get(name)
            if actual_hint is None and parameter_hints:
                actual_hint = next(iter(parameter_hints.values()))
            actual_hint_text = getattr(actual_hint, "__name__", str(actual_hint)) if actual_hint is not None else ""
            if str(expected_hint) not in str(actual_hint_text):
                passed = False
        if "return" in expected:
            return_hint = hints.get("return", signature.return_annotation)
            if str(expected["return"]) not in str(return_hint):
                passed = False
        if "return" not in expected and signature.return_annotation is inspect.Signature.empty:
            passed = False
    except Exception as error:
        return {"status": "failed", "reason": "type_hint_check_error", "stderr": str(error)}
    return {
        "status": "passed" if passed else "failed",
        "reason": "type_hint_check",
        "actual": {key: str(value) for key, value in hints.items()},
        "expected": expected,
        "stderr": "",
    }


def _run_python_performance_assertion(assertion: dict, function, entry_name: str) -> dict:
    expectation = assertion.get("expectation", {})
    value = assertion.get("value", {})
    metadata = expectation.get("metadata", {})
    if isinstance(expectation, dict) and expectation:
        value = {
            "input_size": metadata.get("input_size", value.get("input_size", 0)),
            "max_seconds": metadata.get("max_runtime_seconds", value.get("max_seconds", 0)),
        }
    if not isinstance(value, dict):
        return {"status": "skipped", "reason": "invalid_performance_schema", "stderr": ""}
    input_size = int(value.get("input_size", 0) or 0)
    max_seconds = float(value.get("max_seconds", 0) or 0)
    if input_size <= 0 or max_seconds <= 0:
        return {"status": "skipped", "reason": "missing_performance_parameters", "stderr": ""}
    numbers = [random.randint(-100000, 100000) for _ in range(input_size)]
    kwargs = {}
    if "reverse" in str(assertion.get("description", "")).lower():
        kwargs["reverse"] = True
    started = time.perf_counter()
    try:
        function(numbers, **kwargs)
    except TypeError:
        function(numbers)
    elapsed = time.perf_counter() - started
    return {
        "status": "passed" if elapsed <= max_seconds else "failed",
        "reason": "performance_check",
        "actual": elapsed,
        "expected": max_seconds,
        "stderr": "",
    }


def _run_python_structured_assertion(assertion: dict, function) -> dict:
    call_spec = assertion.get("call", {})
    expectation = assertion.get("expectation", {})
    if isinstance(call_spec, dict) and isinstance(expectation, dict) and expectation:
        normalized = {
            "args": [_safe_literal_eval(item) for item in call_spec.get("args", [])],
            "kwargs": {
                str(key): _safe_literal_eval(item)
                for key, item in dict(call_spec.get("kwargs", {})).items()
            },
            "expected": _safe_literal_eval(expectation.get("expected")),
            "comparator": str(expectation.get("kind", "equals")),
        }
        value = {}
    else:
        value = assertion.get("value", {})
        if not isinstance(value, dict):
            return {"status": "skipped", "reason": "invalid_behavior_schema", "stderr": ""}
        if value.get("testable_via_integers") is False:
            return {"status": "skipped", "reason": "explicitly_not_testable", "stderr": ""}
        normalized = _normalize_call_spec(value)
    pre_call_input = normalized["args"][0] if normalized["args"] else None
    if pre_call_input is None:
        list_like_values = [item for item in normalized["kwargs"].values() if isinstance(item, list)]
        pre_call_input = list_like_values[0] if list_like_values else None
    input_snapshot = list(pre_call_input) if isinstance(pre_call_input, list) else pre_call_input
    expectation_kind = str(expectation.get("kind", ""))
    positional_args = list(normalized["args"])
    actual = None
    raised_error: Exception | None = None
    if expectation_kind == "raises":
        ordered_kwargs = dict(normalized["kwargs"])
        positional_args = list(normalized["args"])
        try:
            function(*positional_args, **ordered_kwargs)
        except Exception as error:  # noqa: BLE001
            raised_error = error
    else:
        actual, positional_args, call_error = _call_python_function(function, normalized["kwargs"], normalized["args"])
        if call_error:
            return {"status": "failed", "reason": "function_call_error", "stderr": call_error}
    checks = value.get("checks", [])
    if not isinstance(checks, list):
        checks = []

    input_reference = positional_args[0] if positional_args else None
    passed = True
    expected = normalized["expected"]
    comparator = normalized["comparator"]
    if expectation_kind == "raises":
        expected_exception_type = ""
        if isinstance(expected, dict):
            expected_exception_type = str(
                expected.get("exception_type") or expected.get("raises") or ""
            )
        passed = raised_error is not None
        if expected_exception_type:
            passed = passed and expected_exception_type in type(raised_error).__name__
        return {
            "status": "passed" if passed else "failed",
            "reason": "structured_behavior_check",
            "actual": type(raised_error).__name__ if raised_error is not None else None,
            "expected": expected,
            "stderr": "" if raised_error is None else str(raised_error),
        }

    if expectation_kind not in {"input_unchanged", "new_object"} and expected is not None:
        passed = passed and _compare_value(actual, expected, comparator)
    if expectation_kind == "input_unchanged" and input_reference is not None:
        metadata = expectation.get("metadata", {})
        expected_after = metadata.get("expected_after", input_snapshot) if isinstance(metadata, dict) else input_snapshot
        passed = passed and (input_reference == expected_after)
    if expectation_kind == "new_object" and input_reference is not None:
        passed = passed and (actual is not input_reference)
    if value.get("output_is_new_object") is True or value.get("type") == "identity":
        if input_reference is not None:
            passed = passed and (actual is not input_reference)
    if value.get("original_list_unchanged") is True:
        passed = passed and (input_reference == input_snapshot)
    expected_dict = value.get("expected", {})
    if isinstance(expected_dict, dict):
        if expected_dict.get("input_unchanged") is True and input_reference is not None:
            passed = passed and (input_reference == input_snapshot)
        if expected_dict.get("is_not_same_as") == "input" and input_reference is not None:
            passed = passed and (actual is not input_reference)
    if "no_mutation" in checks or "original_unchanged" in checks:
        if input_reference is not None:
            passed = passed and (input_reference == input_snapshot)

    return {
        "status": "passed" if passed else "failed",
        "reason": "structured_behavior_check",
        "actual": actual,
        "expected": expected,
        "stderr": "",
    }


def _load_python_entry(entry_name: str):
    spec = importlib.util.spec_from_file_location("packaged_solution", CODE_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot_load_python_solution")
    module = importlib.util.module_from_spec(spec)
    sys.modules["packaged_solution"] = module
    spec.loader.exec_module(module)
    fn = getattr(module, entry_name, None)
    if not callable(fn):
        raise RuntimeError(f"entry_not_callable:{entry_name}")
    return fn


def _run_program_io(spec_path: Path) -> dict:
    spec = _read_json(spec_path)
    point_dir = spec_path.parent
    command = _program_command(str(spec.get("language", "")))
    details = []
    passed = True
    inputs = sorted((point_dir / "io_cases").glob("input_*.txt"))
    outputs = sorted((point_dir / "io_cases").glob("expected_output_*.txt"))
    for input_path, output_path in zip(inputs, outputs):
        completed = subprocess.run(
            command,
            input=input_path.read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            cwd=WORKSPACE,
        )
        expected = _normalize_text(output_path.read_text(encoding="utf-8"))
        actual = _normalize_text(completed.stdout)
        case_passed = completed.returncode == 0 and actual == expected
        passed = passed and case_passed
        details.append(
            {
                "input_file": input_path.name,
                "expected_file": output_path.name,
                "expected_output": expected,
                "actual_output": actual,
                **_completed_record(completed),
                "passed": case_passed,
            }
        )
    return {
        "status": "passed" if passed else "failed",
        "passed": passed,
        "details": details,
    }


def _run_python_function_call(spec_path: Path, spec: dict) -> dict:
    entry_name = str((spec.get("target_signature") or {}).get("entry_name", ""))
    function = _load_python_entry(entry_name)
    details = []
    failed = False
    executed = False
    for assertion in spec.get("assertions", []):
        kind = str(assertion.get("kind", ""))
        value = assertion.get("value", {})
        if isinstance(value, dict) and (
            value.get("test_code")
            or value.get("pre_call")
            or value.get("post_call_check")
            or value.get("setup")
        ):
            result = _run_python_exec_assertion(assertion, function, entry_name)
        elif isinstance(value, dict) and value.get("check_type") == "type_hints":
            result = _run_python_type_hint_assertion(assertion, function)
        elif kind == "performance":
            result = _run_python_performance_assertion(assertion, function, entry_name)
        elif kind == "behavior":
            result = _run_python_structured_assertion(assertion, function)
        else:
            result = {"status": "skipped", "reason": f"unsupported_assertion_kind:{kind}", "stderr": ""}
        status = str(result.get("status", "skipped"))
        if status in {"passed", "failed"}:
            executed = True
        if status == "failed":
            failed = True
        details.append(
            {
                "assertion_id": assertion.get("assertion_id", ""),
                "description": assertion.get("description", ""),
                "status": status,
                "reason": result.get("reason", ""),
                "expected": result.get("expected"),
                "actual": result.get("actual"),
                "stderr": result.get("stderr", ""),
                "passed": status == "passed",
            }
        )
    if not details or not executed:
        return {"status": "skipped", "passed": True, "details": details or [{"reason": "no_executable_assertions"}]}
    return {
        "status": "failed" if failed else "passed",
        "passed": not failed,
        "details": details,
    }


def _run_node_function_call(spec: dict, target_path: Path) -> dict:
    entry_name = str((spec.get("target_signature") or {}).get("entry_name", ""))
    details = []
    passed = True
    node_script = \"\"\"const payload = JSON.parse(process.argv[1]);
const mod = require(payload.module_path);
const fn = mod[payload.entry_name] || (mod.default && mod.default[payload.entry_name]) || mod.default;
if (typeof fn !== 'function') {
  console.log(JSON.stringify({ok: false, error: 'entry_not_callable'}));
  process.exit(2);
}
let callArgs = payload.args;
if ((!callArgs || callArgs.length === 0) && payload.kwargs && Object.keys(payload.kwargs).length > 0) {
  callArgs = [payload.kwargs];
}
Promise.resolve(fn(...callArgs))
  .then((result) => console.log(JSON.stringify({ok: true, result})))
  .catch((error) => {
    console.log(JSON.stringify({ok: false, error: String(error)}));
    process.exit(3);
  });\"\"\"
    for assertion in spec.get("assertions", []):
        if assertion.get("kind") != "behavior":
            continue
        behavior_case = _extract_behavior_case(assertion)
        payload = json.dumps(
            {
                "module_path": str(target_path),
                "entry_name": entry_name,
                "args": behavior_case["args"],
                "kwargs": behavior_case["kwargs"],
            }
        )
        completed = subprocess.run(
            ["node", "-e", node_script, payload],
            text=True,
            capture_output=True,
            cwd=WORKSPACE,
        )
        response_text = (completed.stdout or "").strip()
        actual = None
        stderr = completed.stderr or ""
        try:
            response = json.loads(response_text) if response_text else {}
            actual = response.get("result")
            if response.get("error"):
                stderr = response.get("error")
        except json.JSONDecodeError:
            stderr = "\\n".join(part for part in [stderr, response_text] if part).strip()
        case_passed = completed.returncode == 0 and _compare_value(
            actual,
            behavior_case["expected"],
            behavior_case["comparator"],
        )
        passed = passed and case_passed
        details.append(
            {
                "assertion_id": behavior_case["assertion_id"],
                "description": behavior_case["description"],
                "args": behavior_case["args"],
                "kwargs": behavior_case["kwargs"],
                "expected": behavior_case["expected"],
                "actual": actual,
                "comparator": behavior_case["comparator"],
                "stderr": stderr,
                **_completed_record(completed),
                "passed": case_passed,
            }
        )
    if not details:
        return {"status": "skipped", "passed": True, "details": [{"reason": "no_behavior_assertions"}]}
    return {
        "status": "passed" if passed else "failed",
        "passed": passed,
        "details": details,
    }


def _run_function_call(spec_path: Path) -> dict:
    spec = _read_json(spec_path)
    language = str(spec.get("language", ""))
    if language == "python":
        return _run_python_function_call(spec_path, spec)
    if language == "javascript":
        return _run_node_function_call(spec, CODE_FILE)
    if language == "typescript":
        return _run_node_function_call(spec, BUILD_DIR / f"{CODE_FILE.stem}.js")
    return {
        "status": "skipped",
        "passed": True,
        "details": [{"reason": f"function_call_auto_runner_not_ready_for_{language}"}],
    }


def _run_non_functional(spec_path: Path) -> dict:
    checker_path = spec_path.parent / "check_non_functional.py"
    if not checker_path.exists():
        return {"status": "skipped", "passed": True, "details": [{"reason": "missing_check_non_functional.py"}]}
    completed = subprocess.run(
        ["python3", str(checker_path)],
        text=True,
        capture_output=True,
        cwd=str(spec_path.parent),
    )
    passed = completed.returncode == 0
    return {
        "status": "passed" if passed else "failed",
        "passed": passed,
        "details": [_completed_record(completed)],
    }


def main() -> int:
    results = []
    failed = False
    for spec_path in sorted(TESTS_DIR.rglob("spec.json")):
        spec = _read_json(spec_path)
        point_id = str(spec.get("point_id", spec_path.parent.name))
        mode = str(spec.get("execution_mode", ""))
        language = str(spec.get("language", ""))
        print(f"[point] {point_id} mode={mode} language={language}")
        if mode == "program_io":
            result = _run_program_io(spec_path)
        elif mode == "function_call":
            result = _run_function_call(spec_path)
        else:
            result = _run_non_functional(spec_path)
        print(f"[{result['status']}] {point_id}")
        if result["status"] == "failed":
            failed = True
        results.append({"point_id": point_id, "mode": mode, "language": language, **result})
    REPORT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _render_python_evaluation_runner(language: str, code_filename: str) -> str:
    compile_command = json.dumps(_render_compile_script(language, code_filename).strip())
    test_command = json.dumps("python3 /workspace/scripts/run_packaged_tests.py")
    return f"""import json
import subprocess
from pathlib import Path

WORKSPACE = Path("/workspace")
SUMMARY_PATH = WORKSPACE / "execution_summary.json"
COMPILE_COMMAND = {compile_command}
TEST_COMMAND = {test_command}


def _run_shell(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", "-lc", command],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
    )


def _write_summary(summary: dict) -> None:
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    summary = {{
        "compile_success": False,
        "tests_success": False,
        "has_skipped_tests": False,
        "skipped_count": 0,
        "failed_test_count": 0,
        "passed_test_count": 0,
        "compile_returncode": None,
        "tests_returncode": None,
        "failure_stage": "",
        "failure_message": "",
    }}
    print("[container] compile/setup")
    compile_result = _run_shell(COMPILE_COMMAND)
    summary["compile_returncode"] = compile_result.returncode
    summary["compile_stdout"] = compile_result.stdout
    summary["compile_stderr"] = compile_result.stderr
    summary["compile_success"] = compile_result.returncode == 0
    if not summary["compile_success"]:
        summary["failure_stage"] = "compile"
        summary["failure_message"] = "compile/setup failed"
        _write_summary(summary)
        return 1
    print("[container] run packaged tests")
    tests_result = _run_shell(TEST_COMMAND)
    summary["tests_returncode"] = tests_result.returncode
    summary["tests_stdout"] = tests_result.stdout
    summary["tests_stderr"] = tests_result.stderr
    report_path = WORKSPACE / "test_report.json"
    report = []
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    summary["passed_test_count"] = sum(1 for item in report if item.get("status") == "passed")
    summary["failed_test_count"] = sum(1 for item in report if item.get("status") == "failed")
    summary["skipped_count"] = sum(1 for item in report if item.get("status") == "skipped")
    summary["has_skipped_tests"] = summary["skipped_count"] > 0
    summary["tests_success"] = summary["failed_test_count"] == 0 and tests_result.returncode == 0
    if not summary["tests_success"]:
        summary["failure_stage"] = "tests"
        summary["failure_message"] = "packaged tests failed"
    _write_summary(summary)
    return 0 if summary["tests_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
"""


def package_case_container(
    task_id: str,
    language: str,
    codegen_result: Dict[str, Any],
    testgen_result: Dict[str, Any],
    generated_tests_dir: str,
    output_dir: str,
) -> ContainerPackagingResult:
    container_dir = Path(output_dir) / task_id
    if container_dir.exists():
        shutil.rmtree(container_dir)
    container_dir.mkdir(parents=True, exist_ok=True)
    generated_files: List[str] = []

    code_source_path = Path(str(codegen_result.get("code_file_path", "")))
    code_target_dir = container_dir / "code"
    code_target_dir.mkdir(parents=True, exist_ok=True)
    code_target_path = code_target_dir / code_source_path.name
    shutil.copy2(code_source_path, code_target_path)
    generated_files.append(str(code_target_path))

    adapted_tests_dir = str(codegen_result.get("adapted_tests_dir", "")).strip()
    test_source_dir = Path(adapted_tests_dir) if adapted_tests_dir else Path(generated_tests_dir) / task_id
    if test_source_dir.exists():
        for path in test_source_dir.rglob("*"):
            if path.is_dir():
                continue
            relative = path.relative_to(test_source_dir)
            target = container_dir / "tests" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            generated_files.append(str(target))

    dockerfile_path = container_dir / "Dockerfile"
    _write_text_file(dockerfile_path, _render_dockerfile(language, code_source_path.name))
    generated_files.append(str(dockerfile_path))

    packaged_point_count = len(list(test_source_dir.glob("point_*")))
    manifest_path = container_dir / "manifest.json"
    _write_text_file(
        manifest_path,
        _render_manifest(codegen_result, testgen_result, str(test_source_dir), packaged_point_count),
    )
    generated_files.append(str(manifest_path))

    script_dir = container_dir / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    runner_path = container_dir / "run_all_tests.sh"
    _write_text_file(runner_path, _render_run_all_tests(language, code_source_path.name))
    generated_files.append(str(runner_path))

    python_runner_path = script_dir / "run_packaged_tests.py"
    _write_text_file(python_runner_path, _render_python_test_runner())
    generated_files.append(str(python_runner_path))

    evaluation_runner_path = script_dir / "run_packaged_evaluation.py"
    _write_text_file(evaluation_runner_path, _render_python_evaluation_runner(language, code_source_path.name))
    generated_files.append(str(evaluation_runner_path))

    return ContainerPackagingResult(
        task_id=task_id,
        language=language,
        container_dir=str(container_dir),
        generated_files=generated_files,
        summary={
            "dockerfile": str(dockerfile_path),
            "runner": str(runner_path),
            "manifest": str(manifest_path),
        },
    )

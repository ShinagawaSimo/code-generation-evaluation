import fnmatch
import json
import shlex
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .model_client import call_model
from .models import EvaluationContext


def _repo_root() -> Path:
    return Path.cwd().resolve()


def _safe_path(path_text: str, root: Path) -> Path:
    path = Path(path_text)
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if root == resolved or root in resolved.parents:
        return resolved
    raise ValueError("path_outside_repo")


def _parse_tool_calls(output: str) -> List[Tuple[str, str]]:
    calls: List[Tuple[str, str]] = []
    lines = output.splitlines()
    index = 0
    while index < len(lines) - 1:
        line = lines[index].strip()
        next_line = lines[index + 1].strip()
        if line.startswith("ACTION:") and next_line.startswith("INPUT:"):
            tool = line.split(":", 1)[1].strip()
            tool_input = next_line.split(":", 1)[1].strip()
            calls.append((tool, tool_input))
            index += 2
            continue
        index += 1
    return calls


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def _tool_ls(args: List[str], root: Path) -> str:
    target = args[0] if args else "."
    path = _safe_path(target, root)
    if not path.exists():
        return "ERROR: path_not_found"
    if path.is_file():
        return path.name
    return "\n".join(sorted(p.name for p in path.iterdir()))


def _tool_find(args: List[str], root: Path) -> str:
    target = args[0] if args else "."
    path = _safe_path(target, root)
    pattern = None
    file_only = False
    if "-name" in args:
        idx = args.index("-name")
        if idx + 1 < len(args):
            pattern = args[idx + 1]
    if "-type" in args:
        idx = args.index("-type")
        if idx + 1 < len(args) and args[idx + 1] == "f":
            file_only = True
    matches: List[str] = []
    for item in path.rglob("*"):
        if file_only and not item.is_file():
            continue
        if pattern and not fnmatch.fnmatch(item.name, pattern):
            continue
        matches.append(str(item.relative_to(root)))
    return "\n".join(sorted(matches))


def _tool_rg(args: List[str], root: Path) -> str:
    glob_pattern = None
    pattern = None
    search_root = "."
    index = 0
    while index < len(args):
        token = args[index]
        if token in {"--glob", "-g"} and index + 1 < len(args):
            glob_pattern = args[index + 1]
            index += 2
            continue
        if token.startswith("--glob="):
            glob_pattern = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        if pattern is None:
            pattern = token
        else:
            search_root = token
        index += 1
    if not pattern:
        return "ERROR: pattern_required"
    base = _safe_path(search_root, root)
    matches: List[str] = []
    for file in base.rglob("*"):
        if not file.is_file():
            continue
        if glob_pattern and not fnmatch.fnmatch(str(file.relative_to(base)), glob_pattern):
            continue
        lines = _read_lines(file)
        for line_index, line in enumerate(lines, start=1):
            if pattern in line:
                matches.append(f"{file.relative_to(root)}:{line_index}:{line}")
                if len(matches) >= 200:
                    return "\n".join(matches)
    return "\n".join(matches)


def _tool_cat(args: List[str], root: Path) -> str:
    if not args:
        return "ERROR: path_required"
    path = _safe_path(args[0], root)
    if not path.exists() or not path.is_file():
        return "ERROR: file_not_found"
    return path.read_text(encoding="utf-8", errors="ignore")


def _tool_head(args: List[str], root: Path) -> str:
    count = 10
    path_arg = None
    if args and args[0] == "-n" and len(args) > 2:
        count = int(args[1])
        path_arg = args[2]
    elif args:
        path_arg = args[0]
    if not path_arg:
        return "ERROR: path_required"
    path = _safe_path(path_arg, root)
    lines = _read_lines(path)
    return "\n".join(lines[:count])


def _tool_tail(args: List[str], root: Path) -> str:
    count = 10
    path_arg = None
    if args and args[0] == "-n" and len(args) > 2:
        count = int(args[1])
        path_arg = args[2]
    elif args:
        path_arg = args[0]
    if not path_arg:
        return "ERROR: path_required"
    path = _safe_path(path_arg, root)
    lines = _read_lines(path)
    return "\n".join(lines[-count:])


def _tool_nl(args: List[str], root: Path) -> str:
    if not args:
        return "ERROR: path_required"
    path = _safe_path(args[0], root)
    lines = _read_lines(path)
    return "\n".join(f"{index}\t{line}" for index, line in enumerate(lines, start=1))


def _tool_wc(args: List[str], root: Path) -> str:
    if not args:
        return "ERROR: path_required"
    path = _safe_path(args[-1], root)
    lines = _read_lines(path)
    if "-l" in args:
        return str(len(lines))
    return str(len("\n".join(lines).encode("utf-8")))


def _tool_touch(args: List[str], root: Path) -> str:
    if not args:
        return "ERROR: path_required"
    path = _safe_path(args[0], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return str(path.relative_to(root))


def _tool_mkdir(args: List[str], root: Path) -> str:
    if not args:
        return "ERROR: path_required"
    path = _safe_path(args[0], root)
    path.mkdir(parents=True, exist_ok=True)
    return str(path.relative_to(root))


def _tool_sed(args: List[str], root: Path) -> str:
    if len(args) < 3 or args[0] != "-i":
        return "ERROR: unsupported_sed_format"
    script = args[1]
    target = args[2]
    if not script.startswith("s/") or script.count("/") < 3:
        return "ERROR: unsupported_sed_format"
    parts = script.split("/")
    old = parts[1]
    new = parts[2]
    path = _safe_path(target, root)
    lines = _read_lines(path)
    updated = [line.replace(old, new, 1) for line in lines]
    path.write_text("\n".join(updated), encoding="utf-8")
    return str(path.relative_to(root))


def _execute_tool_call(tool: str, tool_input: str, root: Path) -> str:
    allowed = {
        "ls": _tool_ls,
        "find": _tool_find,
        "rg": _tool_rg,
        "cat": _tool_cat,
        "head": _tool_head,
        "tail": _tool_tail,
        "nl": _tool_nl,
        "wc": _tool_wc,
        "touch": _tool_touch,
        "mkdir": _tool_mkdir,
        "sed": _tool_sed,
    }
    if tool not in allowed:
        return "ERROR: tool_not_allowed"
    tokens = shlex.split(tool_input)
    if tokens and tokens[0] == tool:
        tokens = tokens[1:]
    return allowed[tool](tokens, root)


def generate_output(context: EvaluationContext) -> EvaluationContext:
    """
    Call the model to generate code when no prefilled output exists.
    context: evaluation context containing prompt, api config, and inputs.
    """
    output = context.metrics_inputs.get("model_output")
    if output is None:
        prompt = context.metrics_inputs.get("model_prompt")
        api_config = context.metrics_inputs.get("model_api_config")
        if prompt and api_config:
            user_input = context.metrics_inputs.get("model_input")
            if not user_input and context.model_input:
                user_input = context.model_input
            if not user_input:
                payload = {
                    "task_statement": context.task_original_statement,
                    "input_direct": context.input_direct,
                    "input_indirect": context.input_indirect,
                    "expected_output": context.expected_output,
                }
                payload["case_metadata"] = {
                    "case_id": context.metrics_inputs.get("case_id") or context.instance_id,
                    "case_path": context.metrics_inputs.get("case_path", ""),
                    "language": context.language,
                }
                payload["tool_context"] = {
                    "repo_root": ".",
                    "allowed_tools": [
                        "ls",
                        "find",
                        "rg",
                        "cat",
                        "head",
                        "tail",
                        "nl",
                        "wc",
                        "touch",
                        "mkdir",
                        "sed",
                    ],
                }
                user_input = json.dumps(payload, ensure_ascii=False)
            elif isinstance(user_input, dict):
                user_input.setdefault(
                    "case_metadata",
                    {
                        "case_id": context.metrics_inputs.get("case_id") or context.instance_id,
                        "case_path": context.metrics_inputs.get("case_path", ""),
                        "language": context.language,
                    },
                )
                user_input.setdefault(
                    "tool_context",
                    {
                        "repo_root": ".",
                        "allowed_tools": [
                            "ls",
                            "find",
                            "rg",
                            "cat",
                            "head",
                            "tail",
                            "nl",
                            "wc",
                            "touch",
                            "mkdir",
                            "sed",
                        ],
                    },
                )
                user_input = json.dumps(user_input, ensure_ascii=False)
            tool_enabled = bool(context.metrics_inputs.get("tool_enabled", True))
            tool_max_turns = int(context.metrics_inputs.get("tool_max_turns", 3))
            root = _repo_root()
            tool_trace: List[Dict[str, str]] = []
            try:
                output = call_model(api_config, prompt, user_input)
                if tool_enabled:
                    for _ in range(tool_max_turns):
                        tool_calls = _parse_tool_calls(output)
                        if not tool_calls:
                            break
                        results: List[str] = []
                        for tool_name, tool_input in tool_calls:
                            result = _execute_tool_call(tool_name, tool_input, root)
                            tool_trace.append(
                                {"tool": tool_name, "input": tool_input, "output": result}
                            )
                            results.append(
                                "\n".join(
                                    [
                                        "TOOL_RESULT_START",
                                        f"ACTION: {tool_name}",
                                        f"INPUT: {tool_input}",
                                        "OUTPUT:",
                                        result,
                                        "TOOL_RESULT_END",
                                    ]
                                )
                            )
                        user_input = "\n\n".join([user_input, "\n\n".join(results)])
                        output = call_model(api_config, prompt, user_input)
            except Exception as error:
                context.run_records["model_error"] = str(error)
                context.metrics_inputs["review_notes"] = str(error)
                output = ""
            if tool_trace:
                context.run_records["tool_trace"] = tool_trace
            if output:
                has_code_block = "CODE_START" in output and "CODE_END" in output
                has_fence = "```" in output
                if not has_code_block and not has_fence and _parse_tool_calls(output):
                    context.run_records["model_error"] = "tool_calls_without_code"
                    context.metrics_inputs["review_notes"] = "tool_calls_without_code"
                    output = ""
    context.run_records["raw_output"] = output or ""
    if not context.run_records["raw_output"]:
        context.run_records.setdefault("model_error", "empty_model_output")
    return context


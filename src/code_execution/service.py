import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .models import CodeExecutionResult


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


def _render_manifest(codegen_result: Dict[str, Any], packaged_point_count: int) -> str:
    return json.dumps(
        {
            "task_id": codegen_result["task_id"],
            "language": codegen_result["language"],
            "code_file_path": codegen_result["code_file_path"],
            "code_filename": Path(str(codegen_result["code_file_path"])).name,
            "packaged_point_count": packaged_point_count,
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


def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _render_run_tests_driver() -> str:
    return (Path(__file__).resolve().parent / "templates" / "run_tests.py").read_text(encoding="utf-8")


def _render_python_evaluation_runner(language: str, code_filename: str) -> str:
    compile_command = json.dumps(_render_compile_script(language, code_filename).strip())
    template = (Path(__file__).resolve().parent / "templates" / "run_packaged_evaluation.py").read_text(encoding="utf-8")
    template = template.replace("__COMPILE_COMMAND__", compile_command)
    return template


def _sanitize_name(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", text.strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "case"


def _image_tag(task_id: str, image_tag_prefix: str) -> str:
    return f"{_sanitize_name(image_tag_prefix)}:{_sanitize_name(task_id)}"


def _write_log(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _format_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def _read_execution_summary(summary_path: Path) -> Dict[str, Any]:
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _is_docker_environment_unavailable(output_text: str) -> bool:
    lower = output_text.lower()
    markers = [
        "failed to connect to the docker api",
        "dockerdesktoplinuxengine",
        "daemon is running",
        "cannot find the file specified",
        "error during connect",
        "docker daemon",
    ]
    return any(marker in lower for marker in markers)


def execute_code(
    task_id: str,
    language: str,
    codegen_result: Dict[str, Any],
    generated_tests_dir: str,
    container_output_dir: str,
    execution_config: Dict[str, Any],
    logs_dir: str,
    artifacts_dir: str,
) -> CodeExecutionResult:
    container_dir = Path(container_output_dir) / task_id
    if container_dir.exists():
        shutil.rmtree(container_dir)
    container_dir.mkdir(parents=True, exist_ok=True)

    code_source_path = Path(str(codegen_result.get("code_file_path", "")))
    code_target_dir = container_dir / "code"
    code_target_dir.mkdir(parents=True, exist_ok=True)
    code_target_path = code_target_dir / code_source_path.name
    shutil.copy2(code_source_path, code_target_path)

    packaged_point_count = 0

    test_source_dir = Path(generated_tests_dir) / task_id / "tests"
    if test_source_dir.exists():
        tests_target_dir = container_dir / "tests"
        tests_target_dir.mkdir(parents=True, exist_ok=True)

        all_test_entries: list = []
        merged_execution_mode = ""
        merged_language = ""
        file_counter = 0

        for manifest_path in sorted(test_source_dir.rglob("manifest.json")):
            mode_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            mode_dir = manifest_path.parent
            merged_execution_mode = str(mode_manifest.get("execution_mode", merged_execution_mode))
            merged_language = str(mode_manifest.get("language", merged_language))

            for test_entry in mode_manifest.get("tests", []):
                original_filename = str(test_entry["filename"])
                test_file = mode_dir / original_filename
                if test_file.exists():
                    file_counter += 1
                    suffix = Path(original_filename).suffix
                    new_filename = f"test_{file_counter:02d}{suffix}"
                    shutil.copy2(test_file, tests_target_dir / new_filename)
                    new_entry = dict(test_entry)
                    new_entry["filename"] = new_filename
                    all_test_entries.append(new_entry)

        packaged_point_count = len(all_test_entries)
        if all_test_entries:
            merged_manifest = {
                "execution_mode": merged_execution_mode,
                "language": merged_language,
                "tests": all_test_entries,
            }
            _write_text_file(tests_target_dir / "manifest.json",
                             json.dumps(merged_manifest, ensure_ascii=False, indent=2))

    dockerfile_path = container_dir / "Dockerfile"
    _write_text_file(dockerfile_path, _render_dockerfile(language, code_source_path.name))

    manifest_path = container_dir / "manifest.json"
    _write_text_file(manifest_path, _render_manifest(codegen_result, packaged_point_count))

    script_dir = container_dir / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)

    run_tests_path = script_dir / "run_tests.py"
    _write_text_file(run_tests_path, _render_run_tests_driver())

    evaluation_runner_path = script_dir / "run_packaged_evaluation.py"
    _write_text_file(evaluation_runner_path, _render_python_evaluation_runner(language, code_source_path.name))

    docker_command = str(execution_config.get("docker_command", "docker"))
    image_tag_prefix = str(execution_config.get("image_tag_prefix", "code-generation-eval"))
    build_timeout_seconds = int(execution_config.get("build_timeout_seconds", 600))
    run_timeout_seconds = int(execution_config.get("run_timeout_seconds", 600))
    image_tag = _image_tag(task_id, image_tag_prefix)

    task_log_dir = Path(logs_dir) / task_id
    task_log_dir.mkdir(parents=True, exist_ok=True)
    build_log_path = task_log_dir / "docker_build.log"
    run_log_path = task_log_dir / "docker_run.log"

    task_artifact_dir = Path(artifacts_dir) / task_id
    task_artifact_dir.mkdir(parents=True, exist_ok=True)
    execution_summary_path = task_artifact_dir / "execution_summary.json"

    packaged_evaluation_script = container_dir / "scripts" / "run_packaged_evaluation.py"
    if not packaged_evaluation_script.exists():
        _write_log(run_log_path, "container context is stale or incomplete: missing scripts/run_packaged_evaluation.py\n")
        return CodeExecutionResult(
            task_id=task_id,
            language=language,
            container_dir=str(container_dir),
            compile_success=False,
            tests_success=False,
            failure_message="container context is stale or incomplete: missing scripts/run_packaged_evaluation.py",
            summary={},
        )

    build_command = [docker_command, "build", "-t", image_tag, str(container_dir)]
    run_wrapper = (
        "status=0; "
        "mkdir -p /workspace/execution_artifacts; "
        "python3 /workspace/scripts/run_packaged_evaluation.py || status=$?; "
        "if [ -f /workspace/execution_summary.json ]; then "
        "cp /workspace/execution_summary.json /workspace/execution_artifacts/execution_summary.json; "
        "fi; "
        "exit $status"
    )
    run_command = [
        docker_command,
        "run",
        "--rm",
        "-v",
        f"{task_artifact_dir.resolve()}:/workspace/execution_artifacts",
        image_tag,
        "sh",
        "-lc",
        run_wrapper,
    ]

    try:
        build_result = subprocess.run(
            build_command,
            cwd=str(container_dir),
            text=True,
            capture_output=True,
            timeout=build_timeout_seconds,
        )
    except FileNotFoundError:
        failure_message = (
            f"Docker command not found: {docker_command}. "
            f"Manual build command: {_format_command(build_command)}"
        )
        _write_log(build_log_path, failure_message + "\n")
        return CodeExecutionResult(
            task_id=task_id,
            language=language,
            container_dir=str(container_dir),
            compile_success=False,
            tests_success=False,
            failure_message=failure_message,
            summary={
                "manual_build_command": _format_command(build_command),
                "manual_run_command": _format_command(run_command),
            },
        )
    except subprocess.TimeoutExpired as error:
        build_log = (error.stdout or "") + ("\n" + error.stderr if error.stderr else "")
        _write_log(build_log_path, build_log)
        return CodeExecutionResult(
            task_id=task_id,
            language=language,
            container_dir=str(container_dir),
            compile_success=False,
            tests_success=False,
            failure_message=f"docker build timeout after {build_timeout_seconds}s",
            summary={
                "build_timeout_seconds": build_timeout_seconds,
                "manual_build_command": _format_command(build_command),
            },
        )

    build_log = (build_result.stdout or "") + ("\n" + build_result.stderr if build_result.stderr else "")
    _write_log(build_log_path, build_log)
    if build_result.returncode != 0:
        environment_unavailable = _is_docker_environment_unavailable(build_log)
        failure_message = (
            "docker environment unavailable: start Docker Desktop / daemon, then rerun code_execution"
            if environment_unavailable
            else "docker build failed"
        )
        return CodeExecutionResult(
            task_id=task_id,
            language=language,
            container_dir=str(container_dir),
            compile_success=False,
            tests_success=False,
            failure_message=failure_message,
            summary={
                "build_returncode": build_result.returncode,
                "manual_build_command": _format_command(build_command),
                "manual_run_command": _format_command(run_command),
            },
        )

    try:
        run_result = subprocess.run(
            run_command,
            cwd=str(container_dir),
            text=True,
            capture_output=True,
            timeout=run_timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        run_log = (error.stdout or "") + ("\n" + error.stderr if error.stderr else "")
        _write_log(run_log_path, run_log)
        return CodeExecutionResult(
            task_id=task_id,
            language=language,
            container_dir=str(container_dir),
            compile_success=False,
            tests_success=False,
            failure_message=f"docker run timeout after {run_timeout_seconds}s",
            summary={
                "run_timeout_seconds": run_timeout_seconds,
                "build_returncode": build_result.returncode,
                "manual_run_command": _format_command(run_command),
            },
        )

    run_log = (run_result.stdout or "") + ("\n" + run_result.stderr if run_result.stderr else "")
    _write_log(run_log_path, run_log)
    execution_summary = _read_execution_summary(execution_summary_path)
    compile_success = bool(execution_summary["compile_success"])
    tests_success = bool(execution_summary["tests_success"])
    has_skipped_tests = bool(execution_summary["has_skipped_tests"])
    skipped_count = int(execution_summary["skipped_count"])
    passed_test_count = int(execution_summary["passed_test_count"])
    failed_test_count = int(execution_summary["failed_test_count"])
    failure_message = str(execution_summary["failure_message"]).strip()
    if not failure_message and run_result.returncode in {125, 126, 127}:
        failure_message = "docker run failed before in-container execution"
    if not failure_message and not tests_success:
        failure_message = "packaged tests failed"

    return CodeExecutionResult(
        task_id=task_id,
        language=language,
        container_dir=str(container_dir),
        compile_success=compile_success,
        tests_success=tests_success,
        passed_test_count=passed_test_count,
        failed_test_count=failed_test_count,
        skipped_count=skipped_count,
        has_skipped_tests=has_skipped_tests,
        failure_message=failure_message,
        summary={
            "build_returncode": build_result.returncode,
            "run_returncode": run_result.returncode,
            "manual_build_command": _format_command(build_command),
            "manual_run_command": _format_command(run_command),
        },
    )

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict

from .models import ContainerExecutionResult


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


def _summarize_missing_execution(run_result: subprocess.CompletedProcess[str]) -> str:
    combined = "\n".join(part for part in [run_result.stdout, run_result.stderr] if part).strip()
    if combined:
        first_line = combined.splitlines()[0].strip()
        return f"packaged evaluation did not complete: {first_line}"
    return "packaged evaluation did not complete and no execution summary was produced"


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


def execute_container(
    packaging_result: Dict[str, Any],
    execution_config: Dict[str, Any],
    logs_dir: str,
    artifacts_dir: str,
) -> ContainerExecutionResult:
    task_id = str(packaging_result["task_id"])
    language = str(packaging_result["language"])
    container_dir = Path(str(packaging_result["container_dir"])).resolve()
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
    test_report_path = task_artifact_dir / "test_report.json"
    packaged_evaluation_script = container_dir / "scripts" / "run_packaged_evaluation.py"

    if not packaged_evaluation_script.exists():
        failure_message = (
            "container context is stale or incomplete: missing scripts/run_packaged_evaluation.py. "
            "Rerun container_packaging, then rerun container_execution."
        )
        _write_log(run_log_path, failure_message + "\n")
        return ContainerExecutionResult(
            task_id=task_id,
            language=language,
            image_tag=_image_tag(task_id, image_tag_prefix),
            container_dir=str(container_dir),
            image_build_success=False,
            compile_success=False,
            run_success=False,
            tests_success=False,
            build_log_path=str(build_log_path),
            run_log_path=str(run_log_path),
            execution_summary_path=str(execution_summary_path),
            failure_message=failure_message,
            summary={},
        )

    build_command = [docker_command, "build", "-t", image_tag, str(container_dir)]
    run_wrapper = (
        "status=0; "
        "mkdir -p /workspace/execution_artifacts; "
        "python3 /workspace/scripts/run_packaged_evaluation.py || status=$?; "
        "if [ -f /workspace/test_report.json ]; then "
        "cp /workspace/test_report.json /workspace/execution_artifacts/test_report.json; "
        "fi; "
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
        return ContainerExecutionResult(
            task_id=task_id,
            language=language,
            image_tag=image_tag,
            container_dir=str(container_dir),
            environment_ready=False,
            image_build_success=False,
            compile_success=False,
            run_success=False,
            tests_success=False,
            build_log_path=str(build_log_path),
            run_log_path=str(run_log_path),
            execution_summary_path=str(execution_summary_path),
            failure_message=failure_message,
            summary={
                "manual_build_command": _format_command(build_command),
                "manual_run_command": _format_command(run_command),
            },
        )
    except subprocess.TimeoutExpired as error:
        build_log = (error.stdout or "") + ("\n" + error.stderr if error.stderr else "")
        _write_log(build_log_path, build_log)
        return ContainerExecutionResult(
            task_id=task_id,
            language=language,
            image_tag=image_tag,
            container_dir=str(container_dir),
            environment_ready=False,
            image_build_success=False,
            compile_success=False,
            run_success=False,
            tests_success=False,
            build_log_path=str(build_log_path),
            run_log_path=str(run_log_path),
            execution_summary_path=str(execution_summary_path),
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
            "docker environment unavailable: start Docker Desktop / daemon, then rerun container_execution"
            if environment_unavailable
            else "docker build failed"
        )
        return ContainerExecutionResult(
            task_id=task_id,
            language=language,
            image_tag=image_tag,
            container_dir=str(container_dir),
            environment_ready=not environment_unavailable,
            image_build_success=False,
            compile_success=False,
            run_success=False,
            tests_success=False,
            build_log_path=str(build_log_path),
            run_log_path=str(run_log_path),
            execution_summary_path=str(execution_summary_path),
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
        return ContainerExecutionResult(
            task_id=task_id,
            language=language,
            image_tag=image_tag,
            container_dir=str(container_dir),
            environment_ready=True,
            image_build_success=True,
            compile_success=False,
            run_success=False,
            tests_success=False,
            build_log_path=str(build_log_path),
            run_log_path=str(run_log_path),
            execution_summary_path=str(execution_summary_path),
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
    run_success = bool(execution_summary) or run_result.returncode == 0
    failure_message = str(execution_summary["failure_message"]).strip()
    if not execution_summary and run_result.returncode != 0:
        failure_message = _summarize_missing_execution(run_result)
    elif not failure_message and run_result.returncode in {125, 126, 127}:
        failure_message = "docker run failed before in-container execution"
    if not failure_message and not tests_success:
        failure_message = "packaged tests failed"

    return ContainerExecutionResult(
        task_id=task_id,
        language=language,
        image_tag=image_tag,
        container_dir=str(container_dir),
        environment_ready=True,
        image_build_success=True,
        compile_success=compile_success,
        run_success=run_success,
        tests_success=tests_success,
        has_skipped_tests=has_skipped_tests,
        skipped_count=skipped_count,
        passed_test_count=passed_test_count,
        failed_test_count=failed_test_count,
        build_log_path=str(build_log_path),
        run_log_path=str(run_log_path),
        execution_summary_path=str(execution_summary_path),
        failure_message=failure_message,
        summary={
            "build_returncode": build_result.returncode,
            "run_returncode": run_result.returncode,
            "test_report_path": str(test_report_path) if test_report_path.exists() else "",
            "manual_build_command": _format_command(build_command),
            "manual_run_command": _format_command(run_command),
            "execution_summary": execution_summary,
        },
    )

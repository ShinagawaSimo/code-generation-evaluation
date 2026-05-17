import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Judge0 internal language identifiers: https://ce.judge0.com/languages
_LANGUAGE_IDS = {
    "python": 71,
    "javascript": 63,
    "typescript": 94,
    "java": 62,
    "c": 50,
    "cpp": 54,
    "go": 95,
    "rust": 73,
}

_DEFAULT_COMPOSE_DIR = Path(__file__).resolve().parents[2] / "docker" / "judge0"
_DEFAULT_BASE_URL = "http://localhost:2358"


@dataclass
class Judge0Result:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    wall_time: float = 0.0
    memory_kb: int = 0
    compile_output: str = ""
    ok: bool = False
    error: str = ""


def _run_docker_compose(compose_dir: str, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose"] + args,
        cwd=compose_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def start_judge0(compose_dir: str | Path | None = None) -> bool:
    directory = str(compose_dir or _DEFAULT_COMPOSE_DIR)
    result = _run_docker_compose(directory, ["up", "-d", "--pull", "missing"], timeout=120)
    return result.returncode == 0


def stop_judge0(compose_dir: str | Path | None = None) -> bool:
    directory = str(compose_dir or _DEFAULT_COMPOSE_DIR)
    result = _run_docker_compose(directory, ["down"], timeout=60)
    return result.returncode == 0


def is_judge0_running(base_url: str | None = None) -> bool:
    url = base_url or _DEFAULT_BASE_URL
    try:
        resp = requests.get(f"{url}/about", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def _language_id(language: str) -> int:
    lid = _LANGUAGE_IDS.get(language.lower())
    if lid is None:
        raise ValueError(f"Unsupported language for Judge0: {language}")
    return lid


def submit_and_wait(
    code: str,
    stdin: str,
    language: str,
    cpu_time_limit: float = 10.0,
    wall_time_limit: float = 20.0,
    memory_limit_kb: int = 256000,
    base_url: str | None = None,
    poll_interval: float = 0.2,
) -> Judge0Result:
    url = base_url or _DEFAULT_BASE_URL
    payload = {
        "source_code": code,
        "stdin": stdin,
        "language_id": _language_id(language),
        "cpu_time_limit": cpu_time_limit,
        "wall_time_limit": wall_time_limit,
        "memory_limit": memory_limit_kb,
        "redirect_stderr_to_stdout": False,
    }
    try:
        resp = requests.post(f"{url}/submissions?wait=false", json=payload, timeout=10)
        resp.raise_for_status()
        token = resp.json()["token"]
    except requests.RequestException as e:
        return Judge0Result(error=f"submission failed: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        return Judge0Result(error=f"bad response: {e}")

    # Judge0 status ids >= 3 mean execution finished (Accepted=3, WA=4, TLE=5, etc.)
    # Status 1=In Queue, 2=Processing — we keep polling until the verdict lands.
    deadline = time.perf_counter() + wall_time_limit + 10
    while time.perf_counter() < deadline:
        try:
            resp = requests.get(f"{url}/submissions/{token}", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            status_id = data.get("status", {}).get("id", 0)
            if status_id >= 3:
                return _parse_result(data)
        except requests.RequestException:
            pass
        time.sleep(poll_interval)

    return Judge0Result(error=f"timeout waiting for result (token={token})")


def batch_submit_and_wait(
    submissions: List[Dict[str, Any]],
    language: str,
    cpu_time_limit: float = 10.0,
    wall_time_limit: float = 20.0,
    memory_limit_kb: int = 256000,
    base_url: str | None = None,
    poll_interval: float = 0.2,
) -> List[Judge0Result]:
    url = base_url or _DEFAULT_BASE_URL
    payload = {
        "submissions": [
            {
                "source_code": s["code"],
                "stdin": s["stdin"],
                "language_id": _language_id(language),
                "cpu_time_limit": cpu_time_limit,
                "wall_time_limit": wall_time_limit,
                "memory_limit": memory_limit_kb,
                "redirect_stderr_to_stdout": False,
            }
            for s in submissions
        ]
    }
    try:
        resp = requests.post(f"{url}/submissions/batch?wait=false", json=payload, timeout=30)
        resp.raise_for_status()
        tokens = [item["token"] for item in resp.json()]
    except requests.RequestException as e:
        return [Judge0Result(error=f"batch submission failed: {e}") for _ in submissions]
    except (json.JSONDecodeError, KeyError) as e:
        return [Judge0Result(error=f"bad batch response: {e}") for _ in submissions]

    # Poll pending submissions concurrently until all finish or deadline is hit.
    results: List[Optional[Judge0Result]] = [None] * len(tokens)
    pending = set(enumerate(tokens))  # (idx, token) pairs still waiting for a verdict
    deadline = time.perf_counter() + wall_time_limit + 15

    while pending and time.perf_counter() < deadline:
        done = set()
        for idx, token in pending:
            try:
                resp = requests.get(
                    f"{url}/submissions/{token}?fields=status,stdout,stderr,exit_code,"
                    f"wall_time,memory,compile_output",
                    timeout=5,
                )
                resp.raise_for_status()
                data = resp.json()
                status_id = data.get("status", {}).get("id", 0)
                if status_id >= 3:
                    results[idx] = _parse_result(data)
                    done.add((idx, token))
            except requests.RequestException:
                pass
        pending -= done
        if pending:
            time.sleep(poll_interval)

    for idx, token in pending:
        results[idx] = Judge0Result(error=f"timeout (token={token})")

    return results


def _parse_result(data: Dict[str, Any]) -> Judge0Result:
    status = data.get("status", {})
    status_id = status.get("id", 0)
    # Status 3 = Accepted: the program ran to completion with exit code 0.
    ok = status_id == 3
    return Judge0Result(
        stdout=data.get("stdout") or "",
        stderr=data.get("stderr") or "",
        exit_code=int(data.get("exit_code") or 0),
        wall_time=float(data.get("wall_time") or 0.0),
        memory_kb=int(data.get("memory") or 0),
        compile_output=data.get("compile_output") or "",
        ok=ok,
    )

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


def build_messages(prompt: str, user_input: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input},
    ]


_DOTENV_LOADED = False


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    content = line.strip()
    if not content or content.startswith("#"):
        return None
    if content.startswith("export "):
        content = content[len("export ") :].strip()
    if "=" not in content:
        return None
    key, value = content.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def _load_dotenv_if_exists() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    candidates = [Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"]
    for dotenv_path in candidates:
        if not dotenv_path.exists() or not dotenv_path.is_file():
            continue
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_dotenv_line(line)
            if not parsed:
                continue
            key, value = parsed
            if key not in os.environ:
                os.environ[key] = value
        return


def resolve_api_key(api_config: Dict[str, Any]) -> str:
    _load_dotenv_if_exists()
    api_key_env = api_config.get("api_key_env", "OPENAI_API_KEY")
    if isinstance(api_key_env, str) and api_key_env.startswith("sk-"):
        return api_key_env
    api_key = os.getenv(str(api_key_env))
    if not api_key:
        raise ValueError(f"Missing API key in environment: {api_key_env}")
    return api_key


def build_api_url(api_config: Dict[str, Any]) -> str:
    provider = api_config.get("provider", "openai")
    if provider == "deepseek":
        base_url = api_config.get("base_url", "https://api.deepseek.com").rstrip("/")
    else:
        base_url = api_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def call_model(api_config: Dict[str, Any], prompt: str, user_input: str) -> str:
    payload = {
        "model": api_config.get("model", "gpt-4.1"),
        "messages": build_messages(prompt, user_input),
    }
    if "temperature" in api_config:
        payload["temperature"] = api_config["temperature"]
    if "max_output_tokens" in api_config:
        payload["max_tokens"] = api_config["max_output_tokens"]
    extra_body = api_config.get("extra_body")
    if isinstance(extra_body, dict):
        payload.update(extra_body)

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(build_api_url(api_config), data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {resolve_api_key(api_config)}")

    timeout = int(api_config.get("timeout_seconds", 60))
    retries = int(api_config.get("timeout_retries", 0))
    backoff_seconds = float(api_config.get("timeout_backoff_seconds", 2))
    last_error: Exception | None = None
    response_body = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
            last_error = None
            break
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8") if error.fp else ""
            raise ValueError(f"Model API error {error.code}: {error_body}") from error
        except (TimeoutError, urllib.error.URLError) as error:
            last_error = error
            if attempt >= retries:
                raise ValueError(
                    f"Model API timeout after {retries + 1} attempt(s): {error}"
                ) from error
            time.sleep(backoff_seconds)
    if last_error is not None:
        raise ValueError(f"Model API timeout after {retries + 1} attempt(s): {last_error}")

    response_json = json.loads(response_body)
    return response_json["choices"][0]["message"]["content"]

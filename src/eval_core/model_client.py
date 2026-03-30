import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List


def _build_messages(prompt: str, user_input: str) -> List[Dict[str, str]]:
    """
    Build chat messages for a single prompt and user input.
    prompt: system prompt content.
    user_input: user message content.
    """
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input},
    ]


def call_model(api_config: Dict[str, Any], prompt: str, user_input: str) -> str:
    """
    Call the model API and return the generated content.
    api_config: API configuration including provider, model, and credentials.
    prompt: system prompt content.
    user_input: user message content.
    """
    provider = api_config.get("provider", "openai")
    api_key_env = api_config.get("api_key_env", "OPENAI_API_KEY")
    api_key = None
    if isinstance(api_key_env, str) and api_key_env.startswith("sk-"):
        api_key = api_key_env
    else:
        api_key = os.getenv(str(api_key_env))
    if not api_key:
        raise ValueError(f"Missing API key in environment: {api_key_env}")

    if provider == "deepseek":
        base_url = api_config.get("base_url", "https://api.deepseek.com").rstrip("/")
    else:
        base_url = api_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
    if base_url.endswith("/v1"):
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": api_config.get("model", "gpt-4.1"),
        "messages": _build_messages(prompt, user_input),
    }
    if "max_output_tokens" in api_config:
        payload["max_tokens"] = api_config.get("max_output_tokens")
    if "temperature" in api_config:
        payload["temperature"] = api_config.get("temperature")
    extra_body = api_config.get("extra_body")
    if isinstance(extra_body, dict):
        payload.update(extra_body)

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {api_key}")

    timeout = api_config.get("timeout_seconds", 60)
    read_timeout = api_config.get("read_timeout_seconds")
    retries = int(api_config.get("timeout_retries", 0))
    backoff_seconds = float(api_config.get("timeout_backoff_seconds", 2))
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if read_timeout is not None:
                    try:
                        response.fp.raw._sock.settimeout(float(read_timeout))
                    except Exception:
                        pass
                body = response.read().decode("utf-8")
            last_error = None
            break
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8") if error.fp else ""
            raise ValueError(f"Model API error {error.code}: {error_body}") from error
        except (TimeoutError, urllib.error.URLError) as error:
            last_error = error
            if attempt >= retries:
                raise ValueError(f"Model API timeout after {retries + 1} attempt(s): {error}") from error
            time.sleep(backoff_seconds)
    if last_error is not None:
        raise ValueError(f"Model API timeout after {retries + 1} attempt(s): {last_error}")
    result = json.loads(body)
    return result["choices"][0]["message"]["content"]

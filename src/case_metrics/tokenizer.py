import re
from typing import Any, Dict, List


def _simple_tokens(text: str) -> List[str]:
    return re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text)


def _tiktoken_tokens(text: str, config: Dict[str, Any]) -> List[str]:
    try:
        import tiktoken
    except ImportError as error:
        raise ValueError("tiktoken is required for tokenizer backend 'tiktoken'") from error

    model_name = str(config.get("tokenizer_model", "gpt-4o-mini"))
    encoding_name = config.get("tokenizer_encoding")
    if encoding_name:
        encoding = tiktoken.get_encoding(str(encoding_name))
    else:
        encoding = tiktoken.encoding_for_model(model_name)
    return [str(token) for token in encoding.encode(text)]


def tokenize(text: str, config: Dict[str, Any]) -> List[str]:
    backend = str(config.get("tokenizer_backend", "tiktoken"))
    if backend == "simple":
        return _simple_tokens(text)
    if backend == "tiktoken":
        return _tiktoken_tokens(text, config)
    raise ValueError(f"Unsupported tokenizer backend: {backend}")


def count_tokens(text: str, config: Dict[str, Any]) -> int:
    return len(tokenize(text, config))

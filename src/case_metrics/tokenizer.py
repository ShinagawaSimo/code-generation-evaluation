from typing import Any, Dict, List


def _tiktoken_tokens(text: str, config: Dict[str, Any]) -> List[str]:
    try:
        import tiktoken
    except ImportError as error:
        raise ValueError("tiktoken is required") from error

    model_name = str(config.get("tokenizer_model", "gpt-4o-mini"))
    encoding_name = config.get("tokenizer_encoding")
    if encoding_name:
        encoding = tiktoken.get_encoding(str(encoding_name))
    else:
        encoding = tiktoken.encoding_for_model(model_name)
    return [str(token) for token in encoding.encode(text)]


def tokenize(text: str, config: Dict[str, Any]) -> List[str]:
    return _tiktoken_tokens(text, config)


def count_tokens(text: str, config: Dict[str, Any]) -> int:
    return len(tokenize(text, config))

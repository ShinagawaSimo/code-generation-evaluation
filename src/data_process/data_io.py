import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: str) -> Dict[str, Any]:
    """
    Load a JSON file into a dictionary.
    path: filesystem path to the JSON file.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str, data: Dict[str, Any]) -> None:
    """
    Save a dictionary to a JSON file with UTF-8 encoding.
    path: filesystem path to write.
    data: dictionary to serialize.
    """
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: str) -> Dict[str, Any]:
    """
    Load a JSON configuration file.
    path: filesystem path to the config file.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_prompt(path: str) -> str:
    """
    Load a prompt text file.
    path: filesystem path to the prompt file.
    """
    return Path(path).read_text(encoding="utf-8")

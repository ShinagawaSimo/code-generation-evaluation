import json
from pathlib import Path
from typing import Any, Dict


def normalize_programming_language(language_text: str) -> str:
    normalized = language_text.strip().lower()
    mapping = {
        "c": "c",
        "c++": "cpp",
        "cpp": "cpp",
        "python": "python",
        "java": "java",
        "rust": "rust",
        "go": "go",
        "typescript": "typescript",
        "ts": "typescript",
        "javascript": "javascript",
        "js": "javascript",
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported Language header: {language_text}")
    return mapping[normalized]


def load_case(case_path: str | Path, fallback_language: str = "python") -> Dict[str, Any]:
    """Load a case from a JSON file and return standardized fields."""
    path = Path(case_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    language = normalize_programming_language(
        str(data.get("language", fallback_language))
    )
    return {
        "task_id": data.get("task_id", path.stem),
        "language": language,
        "body": data["requirement"],
        "complexity": data.get("complexity", 1),
        "acceptance_standard": data.get("acceptance_standard", {}),
        "relevant_code": data.get("relevant_code", ""),
    }

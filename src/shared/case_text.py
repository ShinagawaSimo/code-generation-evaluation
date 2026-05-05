from typing import Dict


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


def parse_case_text(case_text: str, fallback_language: str) -> Dict[str, str]:
    stripped = case_text.strip()
    if not stripped:
        return {"language": fallback_language, "body": ""}
    lines = stripped.splitlines()
    first_line = lines[0].strip()
    if first_line.lower().startswith("language:"):
        language = normalize_programming_language(first_line.split(":", 1)[1].strip())
        body = "\n".join(lines[1:]).strip()
        return {"language": language, "body": body}
    return {"language": fallback_language, "body": stripped}

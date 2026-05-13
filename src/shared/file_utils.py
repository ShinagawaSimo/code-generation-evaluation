import shutil
from pathlib import Path
from typing import List


def clear_output_files(dir_path: str | Path, patterns: List[str]) -> None:
    """Delete files under dir_path matching any glob pattern.

    Only deletes files matching the given patterns — never touches other files.
    Patterns are matched recursively using Path.glob.
    """
    directory = Path(dir_path)
    if not directory.exists() or not directory.is_dir():
        return
    for pattern in patterns:
        for matched in sorted(directory.glob(pattern)):
            if matched.is_file():
                matched.unlink()
            elif matched.is_dir():
                shutil.rmtree(matched)

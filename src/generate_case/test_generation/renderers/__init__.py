import json
from pathlib import Path
from typing import Any, Dict, List

from ..models import GeneratedTestArtifact
from .base import build_manifest


_RENDERERS = {}


def _import_renderers():
    if _RENDERERS:
        return
    from . import python_function_call, python_program_io
    from . import javascript_function_call, javascript_program_io

    _RENDERERS["python"] = {
        "function_call": python_function_call.render,
        "program_io": python_program_io.render,
    }
    _RENDERERS["javascript"] = {
        "function_call": javascript_function_call.render,
        "program_io": javascript_program_io.render,
    }
    _RENDERERS["typescript"] = {
        "function_call": javascript_function_call.render,
        "program_io": javascript_program_io.render,
    }


def render_tests(spec: Dict[str, Any], output_dir: str) -> List[str]:
    _import_renderers()
    language = str(spec.get("language", "python"))
    execution_mode = str(spec.get("execution_mode", ""))
    target_signature = dict(spec.get("target_signature") or {})
    entry_name = str(target_signature.get("entry_name", ""))
    tests = list(spec.get("tests", []))

    lang_renderers = _RENDERERS.get(language, {})
    render_func = lang_renderers.get(execution_mode)
    if render_func is None:
        return []

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    artifacts: List[GeneratedTestArtifact] = []
    manifest_entries: List[dict] = []

    for test in tests:
        test_id = str(test.get("test_id", "unknown"))
        if execution_mode == "function_call":
            artifact = render_func(test, entry_name)
        else:
            artifact = render_func(test)
        artifacts.append(artifact)
        manifest_entries.append({"test_id": test_id, "filename": artifact.relative_path})

    for artifact in artifacts:
        target = output_dir_path / artifact.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact.content, encoding="utf-8")

    manifest = build_manifest(manifest_entries, execution_mode, language)
    manifest_path = output_dir_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return [str(output_dir_path / a.relative_path) for a in artifacts] + [str(manifest_path)]

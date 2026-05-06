import json
from pathlib import Path
from typing import Any, Dict, List

from .models import GeneratedTestArtifact, RequirementPointTestSpec


def _render_spec_json(spec: RequirementPointTestSpec) -> GeneratedTestArtifact:
    return GeneratedTestArtifact("spec.json", json.dumps(spec.to_dict(), ensure_ascii=False, indent=2))


def _render_program_io_files(spec: RequirementPointTestSpec) -> List[GeneratedTestArtifact]:
    artifacts: List[GeneratedTestArtifact] = []
    for index, case in enumerate(spec.io_cases, start=1):
        artifacts.append(
            GeneratedTestArtifact(
                f"io_cases/input_{index:03d}.txt",
                str(case["input_text"]),
            )
        )
        artifacts.append(
            GeneratedTestArtifact(
                f"io_cases/expected_output_{index:03d}.txt",
                str(case["expected_output_text"]),
            )
        )
    return artifacts


def _render_function_call_files(spec: RequirementPointTestSpec) -> List[GeneratedTestArtifact]:
    entry_name = str(spec.target_signature["entry_name"])
    harness_templates = {
        "python": f"from solution import {entry_name}\n\n# Fill assertion execution using function_cases.json\n",
        "javascript": f"const {{ {entry_name} }} = require('./solution');\n\n// Fill assertion execution using function_cases.json\n",
        "typescript": f"import {{ {entry_name} }} from './solution';\n\n// Fill assertion execution using function_cases.json\n",
        "java": f"// Call {entry_name} from generated solution. See function_cases.json\n",
        "go": f"// Call {entry_name} from generated solution. See function_cases.json\n",
        "rust": f"// Call {entry_name} from generated solution. See function_cases.json\n",
        "c": f"/* Call {entry_name} from generated solution. See function_cases.json */\n",
        "cpp": f"// Call {entry_name} from generated solution. See function_cases.json\n",
    }
    checker_name = {
        "python": "checker.py",
        "javascript": "checker.js",
        "typescript": "checker.ts",
        "java": "Checker.java",
        "go": "checker.go",
        "rust": "checker.rs",
        "c": "checker.c",
        "cpp": "checker.cpp",
    }.get(spec.language, "checker.txt")
    return [
        GeneratedTestArtifact(
            "function_cases.json",
            json.dumps(
                {
                    "language": spec.language,
                    "target_signature": spec.target_signature,
                    "function_contract": spec.function_contract,
                    "test_skeleton": spec.test_skeleton,
                    "assertions": spec.assertions,
                },
                ensure_ascii=False,
                indent=2,
            ),
        ),
        GeneratedTestArtifact(checker_name, harness_templates.get(spec.language, "")),
    ]


def _render_non_function_environment(spec: RequirementPointTestSpec) -> List[GeneratedTestArtifact]:
    return [
        GeneratedTestArtifact(
            "environment.json",
            json.dumps(spec.environment, ensure_ascii=False, indent=2),
        ),
        GeneratedTestArtifact(
            "assertions.json",
            json.dumps(spec.assertions, ensure_ascii=False, indent=2),
        ),
        GeneratedTestArtifact(
            "check_non_functional.py",
            "import json\nfrom pathlib import Path\n\n"
            "environment = json.loads(Path('environment.json').read_text(encoding='utf-8'))\n"
            "assertions = json.loads(Path('assertions.json').read_text(encoding='utf-8'))\n"
            "print({'environment': environment, 'assertions': assertions})\n",
        ),
    ]


def render_point_artifacts(spec: RequirementPointTestSpec) -> List[GeneratedTestArtifact]:
    artifacts = [_render_spec_json(spec)]
    if spec.execution_mode == "program_io":
        artifacts.extend(_render_program_io_files(spec))
    elif spec.execution_mode == "function_call":
        artifacts.extend(_render_function_call_files(spec))
    else:
        artifacts.extend(_render_non_function_environment(spec))
    if spec.test_kind == "non_functional" and spec.execution_mode != "gui_or_server":
        artifacts.extend(_render_non_function_environment(spec))
    return artifacts


def write_point_artifacts(base_dir: str, point_id: str, artifacts: List[GeneratedTestArtifact]) -> List[str]:
    output_paths: List[str] = []
    point_dir = Path(base_dir) / point_id
    point_dir.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        target = point_dir / artifact.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact.content, encoding="utf-8")
        output_paths.append(str(target))
    return output_paths

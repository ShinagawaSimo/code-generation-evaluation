import re
from pathlib import Path
from typing import Any, Dict, List

from shared.model_client import call_model

from .models import ReferenceCodeResult, ReferenceImplementation
from .prompting import build_reference_code_input, load_reference_code_prompt


def _parse_approach_blocks(raw_output: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    pattern = re.compile(
        r"^=== approach ===$\n(?P<header>.*?)^--- code ---$\n(?P<code>.*?)^--- end approach ===",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(raw_output):
        header_text = match.group("header").strip()
        code_text = match.group("code").strip()
        metadata: Dict[str, Any] = {}
        parameters: List[Dict[str, Any]] = []
        for line in header_text.splitlines():
            line = line.strip()
            if line.startswith("parameters:"):
                continue
            if line.startswith("- name:"):
                param = {}
                for part in line.strip("- ").split(","):
                    kv = part.split(":", 1)
                    if len(kv) == 2:
                        param[kv[0].strip()] = kv[1].strip()
                if param:
                    parameters.append(param)
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        if "approach_id" in metadata or code_text:
            metadata["parameters"] = parameters
            metadata["code_text"] = code_text
            blocks.append(metadata)
    return blocks


def generate_reference_code(
    task_id: str,
    language: str,
    original_requirement_text: str,
    api_config: Dict[str, Any],
    code_output_dir: str,
    prompt_text: str | None = None,
    relevant_code: str = "",
) -> ReferenceCodeResult:
    prompt = prompt_text or load_reference_code_prompt()
    user_input = build_reference_code_input(language, original_requirement_text, relevant_code)
    raw_output, *_ = call_model(api_config, prompt, user_input)

    approach_blocks = _parse_approach_blocks(raw_output)
    if len(approach_blocks) > 5:
        print(
            f"[reference_code_generation] task={task_id} "
            f"capping approaches from {len(approach_blocks)} to 5"
        )
        approach_blocks = approach_blocks[:5]

    output_dir = Path(code_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    implementations: List[ReferenceImplementation] = []
    for block in approach_blocks:
        approach_id = str(block.get("approach_id", ""))
        code_text = str(block.get("code_text", ""))
        file_name = f"{task_id}_{approach_id}.py" if approach_id else f"{task_id}_{len(implementations)+1:03d}.py"
        file_path = output_dir / file_name
        file_path.write_text(code_text, encoding="utf-8")

        implementations.append(
            ReferenceImplementation(
                approach_id=approach_id,
                approach_name=str(block.get("approach_name", "")),
                description=str(block.get("description", "")),
                code_file_path=str(file_path),
                interface_type=str(block.get("interface_type", "function_call")),
                entry_name=str(block.get("entry_name", "")),
                parameters=block.get("parameters", []),
                return_type=str(block.get("return_type", "")),
                approach_metadata={
                    "algorithm_type": block.get("algorithm_type", ""),
                    "time_complexity": block.get("time_complexity", ""),
                    "space_complexity": block.get("space_complexity", ""),
                    "key_characteristics": block.get("key_characteristics", ""),
                },
            )
        )

    print(
        f"[reference_code_generation] task={task_id} "
        f"implementations={len(implementations)} "
        f"output_dir={code_output_dir}"
    )
    return ReferenceCodeResult(
        task_id=task_id,
        language=language,
        code_output_dir=code_output_dir,
        implementations=implementations,
    )

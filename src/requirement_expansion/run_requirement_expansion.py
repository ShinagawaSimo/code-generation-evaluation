import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from requirement_expansion.case_io import (
    build_result_path,
    list_case_paths,
    load_case_request,
    load_json,
    save_result,
)
from requirement_expansion.prompting import get_requirement_expansion_prompt
from requirement_expansion.service import expand_requirement


def run_requirement_expansion() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pipeline_config = load_json(str(project_root / "config" / "requirement_expansion.json"))
    api_config = load_json(str(project_root / "config" / "model_api.json"))
    prompt_text = get_requirement_expansion_prompt(str(project_root / pipeline_config["prompt_path"]))

    case_paths = list_case_paths(
        str(project_root / pipeline_config["cases_dir"]),
        str(pipeline_config["case_glob"]),
    )
    case_defaults = dict(pipeline_config.get("case_defaults", {}))
    results_dir = str(project_root / pipeline_config["results_dir"])
    raw_output_dir = str(project_root / pipeline_config["raw_output_dir"])
    total_cases = len(case_paths)
    print(f"[requirement_expansion] start total_cases={total_cases}")

    for case_index, case_path in enumerate(case_paths, start=1):
        print(f"[requirement_expansion] case {case_index}/{total_cases} path={case_path}")
        request = load_case_request(str(case_path), defaults=case_defaults)
        print(f"[requirement_expansion] task={request.task_id} language={request.language}")
        result = expand_requirement(request, api_config, prompt_text=prompt_text)
        raw_output_path = Path(raw_output_dir) / f"{request.task_id}.txt"
        raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_output_path.write_text(result.raw_response, encoding="utf-8")
        result.summary.setdefault("case_path", str(case_path))
        result.summary.setdefault("raw_output_path", str(raw_output_path))
        save_result(str(build_result_path(results_dir, request.task_id)), result)
        print(
            f"[requirement_expansion] done task={request.task_id} points={len(result.requirement_points)} "
            f"result={build_result_path(results_dir, request.task_id)}"
        )
    print("[requirement_expansion] complete")


if __name__ == "__main__":
    run_requirement_expansion()

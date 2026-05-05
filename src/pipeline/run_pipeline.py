import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_metrics.case_io import load_json
from code_generation.run_code_generation import run_code_generation
from container_execution.run_container_execution import run_container_execution
from container_packaging.run_container_packaging import run_container_packaging
from case_metrics.run_case_metrics import run_case_metrics
from requirement_expansion.run_requirement_expansion import run_requirement_expansion
from test_generation.run_test_generation import run_test_generation


def run_pipeline() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pipeline_config = load_json(str(project_root / "config" / "pipeline.json"))
    stages = list(pipeline_config.get("stages", []))
    total_stages = len(stages)
    print(f"[pipeline] start total_stages={total_stages}")
    for stage_index, stage_name in enumerate(stages, start=1):
        print(f"[pipeline] stage {stage_index}/{total_stages} name={stage_name}")
        if stage_name == "requirement_expansion":
            run_requirement_expansion()
        elif stage_name == "case_metrics":
            run_case_metrics()
        elif stage_name == "test_generation":
            run_test_generation()
        elif stage_name == "code_generation":
            run_code_generation()
        elif stage_name == "container_packaging":
            run_container_packaging()
        elif stage_name == "container_execution":
            run_container_execution()
        else:
            raise ValueError(f"Unsupported pipeline stage: {stage_name}")
        print(f"[pipeline] stage done name={stage_name}")
    print("[pipeline] complete")


if __name__ == "__main__":
    run_pipeline()

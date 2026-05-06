import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_metrics.case_io import load_json
from case_metrics.run_case_metrics import run_case_metrics
from case_spec_generation.run_case_spec_generation import run_case_spec_generation
from pipeline.run_case_summary import run_case_summary
from reference_code_generation.run_reference_code_generation import run_reference_code_generation
from test_generation.run_test_generation import run_test_generation


def run_case_pipeline() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pipeline_config = load_json(str(project_root / "config" / "case_pipeline.json"))
    stages = list(pipeline_config.get("stages", []))
    total_stages = len(stages)
    print(f"[case_pipeline] start total_stages={total_stages}")
    for stage_index, stage_name in enumerate(stages, start=1):
        print(f"[case_pipeline] stage {stage_index}/{total_stages} name={stage_name}")
        if stage_name == "case_spec_generation":
            run_case_spec_generation()
        elif stage_name == "case_metrics":
            run_case_metrics()
        elif stage_name == "test_generation":
            run_test_generation()
        elif stage_name == "reference_code_generation":
            run_reference_code_generation()
        elif stage_name == "case_summary":
            run_case_summary()
        else:
            raise ValueError(f"Unsupported case pipeline stage: {stage_name}")
        print(f"[case_pipeline] stage done name={stage_name}")
    print("[case_pipeline] complete")


if __name__ == "__main__":
    run_case_pipeline()

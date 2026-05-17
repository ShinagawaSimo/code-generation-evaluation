import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.case_metrics.case_io import load_json
from eval_pipeline.code_gen.run_code_generation import run_code_generation
from eval_pipeline.code_exec.run_code_execution import run_code_execution
from eval_pipeline.code_metrics.run_code_metrics import run_code_metrics


def run_codegen_pipeline() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pipeline_config = load_json(str(project_root / "config" / "codegen_pipeline.json"))
    stages = list(pipeline_config.get("stages", []))
    total_stages = len(stages)
    print(f"[codegen_pipeline] start total_stages={total_stages}")
    for stage_index, stage_name in enumerate(stages, start=1):
        print(f"[codegen_pipeline] stage {stage_index}/{total_stages} name={stage_name}")
        if stage_name == "code_generation":
            run_code_generation()
        elif stage_name == "code_execution":
            run_code_execution()
        elif stage_name == "code_metrics":
            run_code_metrics()
        else:
            raise ValueError(f"Unsupported codegen pipeline stage: {stage_name}")
        print(f"[codegen_pipeline] stage done name={stage_name}")
    print("[codegen_pipeline] complete")


if __name__ == "__main__":
    run_codegen_pipeline()

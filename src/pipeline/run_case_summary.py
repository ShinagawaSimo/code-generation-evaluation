import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_metrics.case_io import list_result_paths, load_json
from pipeline.case_summary import generate_case_summary


def run_case_summary() -> None:
    project_root = Path(__file__).resolve().parents[2]
    summary_dir = str(project_root / "artifacts" / "case_summary")

    spec_paths = {
        path.stem: str(path)
        for path in list_result_paths(
            str(project_root / "artifacts" / "case_spec_generation" / "results"),
            "*.json",
        )
    }
    test_paths = {
        path.stem: str(path)
        for path in list_result_paths(
            str(project_root / "artifacts" / "test_generation" / "results"),
            "*.json",
        )
    }
    ref_paths = {
        path.stem: str(path)
        for path in list_result_paths(
            str(project_root / "artifacts" / "reference_code_generation" / "results"),
            "*.json",
        )
    }

    all_task_ids = set(spec_paths.keys()) | set(test_paths.keys()) | set(ref_paths.keys())
    total = len(all_task_ids)
    print(f"[case_summary] start total_cases={total}")

    for task_id in sorted(all_task_ids):
        summary_path = generate_case_summary(
            task_id=task_id,
            spec_result_path=spec_paths.get(task_id, ""),
            test_result_path=test_paths.get(task_id, ""),
            reference_code_result_path=ref_paths.get(task_id, ""),
            summary_dir=summary_dir,
        )
        print(f"[case_summary] done task={task_id} summary={summary_path}")
    print("[case_summary] complete")


if __name__ == "__main__":
    run_case_summary()

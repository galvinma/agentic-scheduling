import sys
from pathlib import Path

import pandas as pd

from app.outputs import write_gantt_chart, write_schedule_csv
from app.solver import build_and_solve

INPUTS_DIR = Path(__file__).parent / "inputs"
OUTPUTS_DIR = Path(__file__).parent / "outputs"


def main():
    teams_path = INPUTS_DIR / "teams.csv"
    requests_path = INPUTS_DIR / "requests.csv"

    if not teams_path.exists():
        print(f"ERROR: {teams_path} not found", file=sys.stderr)
        sys.exit(1)
    if not requests_path.exists():
        print(f"ERROR: {requests_path} not found", file=sys.stderr)
        sys.exit(1)

    teams_df = pd.read_csv(teams_path, index_col="Team")
    requests_df = pd.read_csv(requests_path)

    print(f"Loaded {len(teams_df.columns)} clinicians, {len(requests_df)} weeks")
    print("Solving...")

    schedule, gaps = build_and_solve(teams_df, requests_df)

    if schedule is None:
        print("ERROR: Solver could not find any feasible solution.", file=sys.stderr)
        sys.exit(1)

    if gaps:
        print(f"\nCOVERAGE GAPS in {len(gaps)} week(s):")
        for g in gaps:
            print(f"  - {g}")
    else:
        print("No coverage gaps.")

    OUTPUTS_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUTS_DIR / "schedule.csv"
    png_path = OUTPUTS_DIR / "schedule.png"

    write_schedule_csv(schedule, csv_path)
    write_gantt_chart(schedule, png_path)

    print(f"\nOutputs written to {OUTPUTS_DIR}/")
    print(f"  {csv_path.name}")
    print(f"  {png_path.name}")


if __name__ == "__main__":
    main()
